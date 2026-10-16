"""Compliance validator for Quick Response Code Indonesian Standard (ASPI v1.0 & EMVCo MPM)."""

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Union

from qris_parser.models import ComplianceReport, ParseResult
from qris_parser.spec import (
    MERCHANT_CRITERIA,
    TAG_MAX_LENGTHS,
    get_root_name,
    get_subtag_name,
    is_template_tag,
)


def is_valid_amount(value: str) -> bool:
    """Validate that value is a strictly positive EMVCo amount (max 2 decimal places)."""
    if not re.match(r"^\d+(\.\d{1,2})?$", value):
        return False
    try:
        dec = Decimal(value)
        return dec > Decimal(0)
    except (InvalidOperation, ValueError):
        return False


def check_mpm_compliance(input_data: Union[ParseResult, Dict[str, Any]]) -> ComplianceReport:
    """Audit parsed QRIS payload tags against ASPI v1.0 and EMVCo MPM regulations.

    Args:
        input_data: Either a ParseResult instance or a dictionary of decoded tags.

    Returns:
        ComplianceReport with list of errors and warnings.
    """
    errors: List[str] = []
    warnings: List[str] = []

    tags: Dict[str, Any]
    if isinstance(input_data, ParseResult):
        tags = input_data.tags
        # Structural issues are treated as compliance errors
        errors.extend(input_data.structural_issues)
    else:
        tags = input_data

    def desc(tag: str) -> str:
        return get_root_name(tag)

    def str_val(tag: str) -> Union[str, None]:
        val = tags.get(tag)
        return val if isinstance(val, str) else None

    # 1. Mandatory Tags Check
    mandatory_tags = ["00", "01", "52", "53", "58", "59", "60", "63"]
    for tag in mandatory_tags:
        if tag not in tags:
            errors.append(f"MISSING MANDATORY TAG: [{tag}] {desc(tag)}")

    # 2. Maximum Length & Format Checks
    for tag, value in tags.items():
        max_len = TAG_MAX_LENGTHS.get(tag)
        if max_len is not None and isinstance(value, str) and len(value) > max_len:
            errors.append(f"INVALID LENGTH: [{tag}] {desc(tag)} max length is {max_len}, got {len(value)}")

        if is_template_tag(tag) and isinstance(value, str) and tag.isdigit() and int(tag) <= 64:
            errors.append(f"INVALID FORMAT: [{tag}] {desc(tag)} must be a nested TLV template")

    # 3. Payload Format Indicator (Tag 00)
    pfi = str_val("00")
    if pfi and pfi != "01":
        errors.append(f"INVALID VALUE: [00] Payload Format Indicator must be '01', got '{pfi}'")

    # 4. Point of Initiation Method (Tag 01)
    poi = str_val("01")
    if poi and poi not in ("11", "12"):
        errors.append(f"INVALID VALUE: [01] Point of Initiation must be '11' (Static) or '12' (Dynamic), got '{poi}'")

    # 5. Merchant Category Code (Tag 52)
    mcc = str_val("52")
    if mcc and not re.match(r"^\d{4}$", mcc):
        errors.append(f"INVALID FORMAT: [52] MCC must be 4 digits, got '{mcc}'")

    # 6. Currency Code (Tag 53)
    curr = str_val("53")
    if curr:
        if not re.match(r"^\d{3}$", curr):
            errors.append(f"INVALID FORMAT: [53] Currency must be 3 digits ISO 4217, got '{curr}'")
        elif curr != "360":
            errors.append(f"INVALID VALUE: [53] QRIS domestic currency must be IDR ('360'), got '{curr}'")

    # 7. Transaction Amount (Tag 54)
    amount = str_val("54")
    if amount is not None:
        if not is_valid_amount(amount):
            errors.append(
                f"INVALID FORMAT: [54] Transaction Amount must be positive numeric with at most 2 decimals, got '{amount}'"
            )
        if poi == "11":
            warnings.append("Static QRIS (01=11) should not include fixed amount [54] - amount is filled by customer")
    elif poi == "12":
        errors.append("MISSING MANDATORY TAG: [54] Transaction Amount is mandatory for Dynamic QRIS (01=12)")

    # 8. Tip and Convenience Fee (Tags 55, 56, 57)
    tip = str_val("55")
    fixed_fee = str_val("56")
    pct_fee = str_val("57")
    if tip is None:
        if fixed_fee is not None:
            errors.append("INVALID VALUE: [56] Fixed Fee is not allowed when Tip Indicator [55] is absent")
        if pct_fee is not None:
            errors.append("INVALID VALUE: [57] Percentage Fee is not allowed when Tip Indicator [55] is absent")
    elif tip == "01":
        if fixed_fee is not None or pct_fee is not None:
            errors.append("INVALID VALUE: [55]=01 (Prompted Tip) cannot have pre-set fee tags [56] or [57]")
    elif tip == "02":
        if fixed_fee is None:
            errors.append("MISSING MANDATORY TAG: [56] Convenience Fee (Fixed) is required when [55]='02'")
        elif not is_valid_amount(fixed_fee):
            errors.append(f"INVALID FORMAT: [56] Convenience Fee (Fixed) must be positive amount, got '{fixed_fee}'")
        if pct_fee is not None:
            errors.append("INVALID VALUE: [57] Percentage Fee cannot exist when [55]='02'")
    elif tip == "03":
        if pct_fee is None:
            errors.append("MISSING MANDATORY TAG: [57] Convenience Fee (%) is required when [55]='03'")
        else:
            try:
                pct = float(pct_fee)
                if pct <= 0.0 or pct > 100.0:
                    errors.append(f"INVALID VALUE: [57] Convenience Fee (%) must be between 0 and 100, got '{pct_fee}'")
            except ValueError:
                errors.append(f"INVALID FORMAT: [57] Convenience Fee (%) must be numeric, got '{pct_fee}'")
        if fixed_fee is not None:
            errors.append("INVALID VALUE: [56] Fixed Fee cannot exist when [55]='03'")
    else:
        errors.append(f"INVALID VALUE: [55] Tip Indicator must be '01', '02', or '03', got '{tip}'")

    # 9. Country Code (Tag 58) & Postal Code (Tag 61)
    country = str_val("58")
    if country:
        if not re.match(r"^[A-Z]{2}$", country):
            errors.append(f"INVALID FORMAT: [58] Country Code must be 2 uppercase letters, got '{country}'")
        elif country != "ID":
            warnings.append(f"Country Code [58] is '{country}' - domestic QRIS uses 'ID'")

    if country == "ID":
        if "61" not in tags:
            errors.append("MISSING MANDATORY TAG: [61] Postal Code is mandatory when Country=ID")
        else:
            postal = str_val("61")
            if not postal:
                errors.append("INVALID VALUE: [61] Postal Code cannot be empty")
            elif not re.match(r"^\d{5}$", postal):
                warnings.append(f"Postal Code [61] '{postal}' is not a standard 5-digit Indonesian postal code")

    # 10. Merchant Name (Tag 59) & City (Tag 60)
    name = str_val("59")
    if "59" in tags and (name is None or not name.strip()):
        errors.append("INVALID VALUE: [59] Merchant Name cannot be blank")

    city = str_val("60")
    if "60" in tags and (city is None or len(city) == 0):
        errors.append("INVALID VALUE: [60] Merchant City length must be greater than 0")

    # 11. CRC (Tag 63)
    crc = str_val("63")
    if crc and (len(crc) != 4 or not re.match(r"^[0-9A-Fa-f]{4}$", crc)):
        errors.append(f"INVALID FORMAT: [63] CRC must be 4 hexadecimal characters, got '{crc}'")

    # 12. Domestic Repository NMID (Tag 51)
    if poi == "11" and "51" not in tags:
        errors.append("MISSING MANDATORY TAG: [51] NMID Domestic Central Repository is mandatory for Static QRIS")

    has_mai = any(k.isdigit() and 26 <= int(k) <= 45 for k in tags)
    if not has_mai and "51" not in tags:
        errors.append("MISSING MAI: At least one Merchant Account Information (Tags 26-45 or 51) must exist")

    # 13. Sub-tags inside MAI (Tags 26-51)
    for tag_key, tag_val in tags.items():
        if not tag_key.isdigit():
            continue
        tag_int = int(tag_key)
        if not (26 <= tag_int <= 51):
            continue
        if not isinstance(tag_val, dict):
            continue

        gui = tag_val.get("00")
        if not gui or not isinstance(gui, str):
            errors.append(f"MISSING MANDATORY TAG: [{tag_key}.00] Globally Unique Identifier is required in MAI")
        elif len(gui) > 32:
            errors.append(f"INVALID LENGTH: [{tag_key}.00] Globally Unique Identifier max 32 chars, got {len(gui)}")

        if 26 <= tag_int <= 45:
            mpan = tag_val.get("01")
            if isinstance(mpan, str):
                if not re.match(r"^\d{1,19}$", mpan):
                    errors.append(f"INVALID FORMAT: [{tag_key}.01] Merchant PAN must be up to 19 digits, got '{mpan}'")
            mid = tag_val.get("02")
            if isinstance(mid, str) and len(mid) > 15:
                errors.append(f"INVALID LENGTH: [{tag_key}.02] Merchant ID max 15 characters, got {len(mid)}")

        crit = tag_val.get("03")
        if isinstance(crit, str) and crit not in MERCHANT_CRITERIA:
            warnings.append(f"Merchant criteria [{tag_key}.03] '{crit}' is not standard (UMI/UKE/UME/UBE/URE)")

        if tag_int == 51:
            nmid = tag_val.get("02")
            if not nmid:
                errors.append("MISSING MANDATORY TAG: [51.02] NMID is mandatory inside tag 51")
            elif isinstance(nmid, str) and not re.match(r"^ID\d{10,13}$", nmid):
                warnings.append(f"NMID format [51.02] '{nmid}' is unusual - standard is 'ID' followed by 10-13 digits")

    # 14. Additional Data (Tag 62)
    adf = tags.get("62")
    if isinstance(adf, dict):
        for sub_k, sub_v in adf.items():
            if not sub_k.isdigit() or not isinstance(sub_v, str):
                continue
            sub_int = int(sub_k)
            if 1 <= sub_int <= 8 and len(sub_v) > 25:
                sub_name = get_subtag_name("62", sub_k)
                errors.append(f"INVALID LENGTH: [62.{sub_k}] {sub_name} max 25 characters, got {len(sub_v)}")
            if sub_int == 9 and not re.match(r"^[AME]{1,3}$", sub_v):
                errors.append(
                    f"INVALID VALUE: [62.09] Additional Consumer Data Request must only contain 'A', 'M', or 'E', got '{sub_v}'"
                )

    # 15. Language Template (Tag 64)
    lang = tags.get("64")
    if isinstance(lang, dict):
        pref = lang.get("00")
        if not pref:
            errors.append("MISSING MANDATORY TAG: [64.00] Language Preference is mandatory in Tag 64")
        elif isinstance(pref, str) and not re.match(r"^[A-Za-z]{2}$", pref):
            errors.append(f"INVALID FORMAT: [64.00] Language Preference must be 2 letters ISO 639, got '{pref}'")

        alt_name = lang.get("01")
        if not alt_name:
            errors.append("MISSING MANDATORY TAG: [64.01] Alternate Merchant Name is mandatory in Tag 64")
        elif isinstance(alt_name, str) and len(alt_name) > 25:
            errors.append(f"INVALID LENGTH: [64.01] Alternate Name max 25 characters, got {len(alt_name)}")

        alt_city = lang.get("02")
        if isinstance(alt_city, str) and len(alt_city) > 15:
            errors.append(f"INVALID LENGTH: [64.02] Alternate City max 15 characters, got {len(alt_city)}")

    return ComplianceReport(errors=errors, warnings=warnings)
