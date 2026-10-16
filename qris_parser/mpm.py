"""Merchant-Presented Mode (MPM) TLV parser for QRIS."""

from typing import Any, Dict, List, Optional, Tuple

from qris_parser.crc import calculate_crc16, verify_crc16
from qris_parser.models import ParseResult
from qris_parser.spec import is_template_tag


def _parse_tlv_entries(
    value: str,
    base_offset: int,
    parent_tag: Optional[str],
    issues: List[str],
) -> List[Tuple[str, Any, int]]:
    """Parse raw TLV string into list of (tag, parsed_value, offset)."""
    entries: List[Tuple[str, Any, int]] = []
    index = 0
    while index < len(value):
        offset = base_offset + index
        where = f"position {offset}" if parent_tag is None else f"tag {parent_tag}, position {offset}"

        if index + 4 > len(value):
            issues.append(f"MALFORMED: Remaining data '{value[index:]}' ({where}) is too short for a tag header")
            break

        tag = value[index : index + 2]
        len_str = value[index + 2 : index + 4]

        if not len_str.isdigit():
            issues.append(f"MALFORMED: Invalid length header '{len_str}' for tag '{tag}' at {where}")
            break

        length = int(len_str)
        val_start = index + 4
        val_end = val_start + length

        if val_end > len(value):
            issues.append(
                f"MALFORMED: Tag {tag} ({where}) declares length {length}, "
                f"but only {len(value) - val_start} characters remain"
            )
            break

        sub_val = value[val_start:val_end]

        if is_template_tag(tag, parent_tag):
            sub_entries = _parse_tlv_entries(sub_val, offset + 4, tag, issues)
            _report_duplicates(sub_entries, tag, issues)
            parsed_sub: Dict[str, Any] = {t: v for t, v, _ in sub_entries}
            entries.append((tag, parsed_sub, offset))
        else:
            entries.append((tag, sub_val, offset))

        index = val_end

    return entries


def _report_duplicates(entries: List[Tuple[str, Any, int]], parent_tag: Optional[str], issues: List[str]) -> None:
    seen: Dict[str, int] = {}
    for tag, _, _ in entries:
        seen[tag] = seen.get(tag, 0) + 1
    for tag, count in seen.items():
        if count > 1:
            scope = f" inside tag {parent_tag}" if parent_tag else ""
            issues.append(f"DUPLICATE TAG: [{tag}] appears {count} times{scope} - only last value will be retained")


def _extract_partial_tags(payload: str) -> Optional[Dict[str, Any]]:
    """Best-effort tag extractor for corrupted payloads."""
    if not payload.startswith("000201"):
        return None
    dummy_issues: List[str] = []
    entries = _parse_tlv_entries(payload, 0, None, dummy_issues)
    return {t: v for t, v, _ in entries} if entries else None


def parse_mpm(qr_string_raw: str) -> ParseResult:
    """Parse a QRIS Merchant-Presented Mode (MPM) string.

    Performs structural TLV decoding, duplicate detection, tag ordering check,
    and ISO/IEC 13239 CRC-16 checksum validation.

    Args:
        qr_string_raw: Raw QRIS string (e.g. '000201010211...6304ABCD').

    Returns:
        ParseResult containing decoded tags, structural issues, and CRC status.
    """
    qr_string = qr_string_raw.strip()
    if len(qr_string) < 4:
        return ParseResult(
            is_valid=False,
            raw_data=qr_string,
            error_message="String is too short to be a valid QRIS payload",
        )

    last_63_idx = qr_string.rfind("6304")
    if last_63_idx == -1:
        expected = calculate_crc16(qr_string + "6304")
        return ParseResult(
            is_valid=False,
            raw_data=qr_string,
            error_message="CRC Tag (6304) is missing or malformed",
            partial_tags=_extract_partial_tags(qr_string),
            expected_crc=expected,
            corrected_payload=f"{qr_string}6304{expected}" if qr_string.startswith("000201") else None,
        )

    data_to_calc = qr_string[: last_63_idx + 4]
    if len(qr_string) < last_63_idx + 8:
        expected = calculate_crc16(data_to_calc)
        return ParseResult(
            is_valid=False,
            raw_data=qr_string,
            error_message="CRC value is truncated",
            partial_tags=_extract_partial_tags(data_to_calc),
            expected_crc=expected,
            corrected_payload=data_to_calc + expected,
        )

    crc_provided = qr_string[last_63_idx + 4 : last_63_idx + 8]
    is_crc_valid, crc_utf8, _ = verify_crc16(data_to_calc, crc_provided)

    if not is_crc_valid:
        corrected = data_to_calc + crc_utf8 + qr_string[last_63_idx + 8 :]
        return ParseResult(
            is_valid=False,
            raw_data=qr_string,
            error_message=f"CRC Mismatch! Payload has '{crc_provided}', calculated '{crc_utf8}'",
            partial_tags=_extract_partial_tags(qr_string),
            expected_crc=crc_utf8,
            corrected_payload=corrected,
        )

    issues: List[str] = []
    trailing = qr_string[last_63_idx + 8 :]
    if trailing:
        issues.append(f"TRAILING DATA: {len(trailing)} extra characters found after CRC ('{trailing[:20]}')")

    entries = _parse_tlv_entries(data_to_calc + crc_provided, 0, None, issues)
    _report_duplicates(entries, None, issues)

    if entries and entries[0][0] != "00":
        issues.append("TAG ORDER: [00] Payload Format Indicator must be the first tag")
    if entries and entries[-1][0] != "63":
        issues.append("TAG ORDER: [63] CRC must be the last tag")

    tags_dict = {t: v for t, v, _ in entries}
    return ParseResult(
        is_valid=True,
        tags=tags_dict,
        raw_data=qr_string,
        structural_issues=issues,
    )
