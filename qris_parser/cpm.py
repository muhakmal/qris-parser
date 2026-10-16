"""QRIS Customer-Presented Mode (CPM) BER-TLV parser and validator."""

import base64
import re
from typing import Any, Dict, List, Optional, Tuple

from qris_parser.models import BerTlv, CpmComplianceReport, CpmParseResult
from qris_parser.privacy import mask_cardholder_name
from qris_parser.spec import CPM_BINARY_TAGS


def normalize_base64(raw_data: str) -> str:
    """Normalize Base64 payload by stripping whitespace and repairing missing padding."""
    cleaned = re.sub(r"\s+", "", raw_data)
    remainder = len(cleaned) % 4
    if remainder in (2, 3):
        cleaned += "=" * (4 - remainder)
    return cleaned


def is_cpm(raw_data: str) -> bool:
    """Check if a raw QR string represents a Customer-Presented Mode (CPM) QRIS.

    Per ASPI CPM spec, the payload is Base64 encoded BER-TLV and starts with tag 85
    followed by 'CPV01', which in Base64 starts with 'hQVDUFY'.
    """
    cleaned = normalize_base64(raw_data)
    if cleaned.startswith("hQVDUFY"):
        return True
    try:
        binary = base64.b64decode(cleaned)
        return len(binary) > 0 and binary[0] == 0x85
    except Exception:
        return False


def _read_ber_length(data: bytes, pos: int) -> Tuple[int, int]:
    """Read ASN.1 / BER-TLV length at pos. Returns (length, new_pos)."""
    if pos >= len(data):
        return 0, pos
    first_byte = data[pos]
    pos += 1
    if (first_byte & 0x80) == 0:
        return first_byte, pos

    num_bytes = first_byte & 0x7F
    length = 0
    for _ in range(num_bytes):
        if pos >= len(data):
            break
        length = (length << 8) | data[pos]
        pos += 1
    return length, pos


def parse_ber_tlv(
    data: bytes, pos: int, end: int, warnings: List[str]
) -> List[BerTlv]:
    """Parse BER-TLV binary stream into list of BerTlv objects."""
    tlvs: List[BerTlv] = []
    while pos < end:
        # Skip null or pad bytes
        if data[pos] in (0x00, 0xFF):
            pos += 1
            continue

        tag_start = pos
        first_byte = data[pos]
        pos += 1

        # Multi-byte tag (subsequent bytes have bit 8 set to 1)
        if (first_byte & 0x1F) == 0x1F:
            while pos < end and (data[pos] & 0x80) != 0:
                pos += 1
            if pos < end:
                pos += 1

        tag_bytes = data[tag_start:pos]
        tag_hex = tag_bytes.hex().upper()

        if pos >= end:
            break

        length, pos = _read_ber_length(data, pos)
        if pos + length > end:
            warnings.append(
                f"Tag {tag_hex} declares length {length} exceeding remaining data ({end - pos} bytes)"
            )
            break

        value_bytes = data[pos : pos + length]
        tlvs.append(BerTlv(tag_hex=tag_hex, length=length, value=value_bytes))
        pos += length

    return tlvs


def _map_tlvs(tlvs: List[BerTlv], raw_tlvs_collector: List[BerTlv], warnings: List[str]) -> Dict[str, Any]:
    """Convert parsed BER-TLV list into nested dictionary."""
    result: Dict[str, Any] = {}
    for tlv in tlvs:
        raw_tlvs_collector.append(tlv)
        tag_hex = tlv.tag_hex.upper()

        if tag_hex == "85":
            try:
                result["85"] = tlv.value.decode("ascii")
            except UnicodeDecodeError:
                result["85"] = tlv.value.hex().upper()
        elif tag_hex in ("61", "63", "62", "64"):
            sub_tlvs = parse_ber_tlv(tlv.value, 0, len(tlv.value), warnings)
            result[tag_hex] = _map_tlvs(sub_tlvs, raw_tlvs_collector, warnings)
        elif tag_hex in CPM_BINARY_TAGS:
            result[tag_hex] = tlv.value.hex().upper()
        else:
            try:
                text = tlv.value.decode("ascii")
                # Ensure all characters are printable ASCII
                if all(0x20 <= ord(c) <= 0x7E for c in text):
                    result[tag_hex] = text
                else:
                    result[tag_hex] = tlv.value.hex().upper()
            except UnicodeDecodeError:
                result[tag_hex] = tlv.value.hex().upper()

    return result


def parse_cpm(raw_data: str) -> CpmParseResult:
    """Parse a QRIS Customer-Presented Mode (CPM) payload.

    Args:
        raw_data: Base64-encoded CPM payload string.

    Returns:
        CpmParseResult with decoded tags and structural warnings.
    """
    cleaned = normalize_base64(raw_data)
    if not is_cpm(cleaned):
        return CpmParseResult(
            is_valid=False,
            error_message="Not a valid CPM QRIS (missing 'hQVDUFY' or tag 85 prefix)",
        )

    try:
        binary = base64.b64decode(cleaned)
    except Exception as e:
        return CpmParseResult(is_valid=False, error_message=f"Base64 decode failed: {str(e)}")

    if len(binary) < 7:
        return CpmParseResult(is_valid=False, error_message=f"Decoded data too short ({len(binary)} bytes)")

    raw_tlvs: List[BerTlv] = []
    warnings: List[str] = []

    try:
        top_tlvs = parse_ber_tlv(binary, 0, len(binary), warnings)
        tag_map = _map_tlvs(top_tlvs, raw_tlvs, warnings)
    except Exception as e:
        return CpmParseResult(is_valid=False, error_message=f"BER-TLV parse error: {str(e)}")

    return CpmParseResult(
        is_valid=True,
        tags=tag_map,
        raw_binary=binary,
        raw_tlvs=raw_tlvs,
        structural_warnings=warnings,
    )


def check_cpm_compliance(tags: Dict[str, Any]) -> CpmComplianceReport:
    """Audit parsed CPM tags against ASPI CPM v0.3 specifications."""
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Payload Format Indicator must be 'CPV01'
    pfi = tags.get("85")
    if pfi != "CPV01":
        errors.append(f"Payload Format Indicator (tag 85) must be 'CPV01', got '{pfi}'")

    # 2. Application Template (tag 61) is mandatory
    app_template = tags.get("61")
    if not isinstance(app_template, dict):
        errors.append("Application Template (tag 61) is mandatory but missing")
    else:
        # 3. ADF Name must be 'A0000006022020'
        adf = app_template.get("4F")
        if not adf:
            errors.append("ADF Name (tag 4F) is mandatory inside tag 61")
        elif str(adf).upper() != "A0000006022020":
            errors.append(f"ADF Name (tag 4F) must be 'A0000006022020', got '{adf}'")

        # 4. Application Label must be 'QRISCPM'
        app_label = app_template.get("50")
        if not app_label:
            errors.append("Application Label (tag 50) is mandatory inside tag 61")
        elif app_label != "QRISCPM":
            errors.append(f"Application Label (tag 50) must be 'QRISCPM', got '{app_label}'")

        # 5. Must have Track 2 (57) or Application PAN (5A)
        has_track2 = "57" in app_template
        has_pan = "5A" in app_template
        if not has_track2 and not has_pan:
            errors.append("Either Track 2 (tag 57) or Application PAN (tag 5A) must be present")

        cardholder = app_template.get("5F20")
        if cardholder:
            warnings.append(f"Cardholder Name (tag 5F20): {mask_cardholder_name(str(cardholder))}")

    return CpmComplianceReport(errors=errors, warnings=warnings)
