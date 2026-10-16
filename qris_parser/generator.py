"""QRIS payload generator and mutator (Static to Dynamic conversion & amount injection)."""

import re
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple

from qris_parser.crc import calculate_crc16
from qris_parser.models import GeneratorResult
from qris_parser.mpm import parse_mpm
from qris_parser.validator import is_valid_amount


class Segment:
    """A top-level TLV tag and value segment."""

    def __init__(self, tag: str, value: str):
        self.tag = tag
        self.value = value

    def encode(self) -> str:
        return f"{self.tag}{len(self.value):02d}{self.value}"


def normalize_amount(input_str: str) -> Optional[str]:
    """Normalize user input (e.g. '10.000', '10000,5', 'Rp 25000') into valid EMVCo amount string."""
    if not input_str:
        return None
    s = input_str.strip()
    if s.lower().startswith("rp"):
        s = s[2:].strip()
    s = s.replace(" ", "")

    # Indonesian number style: '.' groups thousands and ',' marks decimals.
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        # e.g. '10.000' is ten thousand, but '10.5' is ten and a half
        if re.match(r"^\d{1,3}(\.\d{3})+$", s):
            s = s.replace(".", "")

    try:
        val = Decimal(s)
        if val <= Decimal(0):
            return None
        # Format decimal without trailing zero noise if integer
        if val == val.to_integral():
            plain = str(int(val))
        else:
            # At most 2 decimal places
            plain = f"{val:.2f}".rstrip("0").rstrip(".")

        if len(plain) <= 13 and is_valid_amount(plain):
            return plain
    except (InvalidOperation, ValueError):
        return None
    return None


def _get_segments(payload: str) -> Optional[List[Segment]]:
    """Extract raw top-level segments from a payload."""
    segments: List[Segment] = []
    i = 0
    while i < len(payload):
        if i + 4 > len(payload):
            return None
        tag = payload[i : i + 2]
        len_str = payload[i + 2 : i + 4]
        if not len_str.isdigit():
            return None
        length = int(len_str)
        if i + 4 + length > len(payload):
            return None
        value = payload[i + 4 : i + 4 + length]
        segments.append(Segment(tag, value))
        i += 4 + length
    return segments


def _rebuild_payload(segments: List[Segment]) -> str:
    """Rebuild payload string and calculate new CRC-16."""
    body = "".join(s.encode() for s in segments if s.tag != "63") + "6304"
    crc = calculate_crc16(body)
    return body + crc


def to_dynamic(payload: str, amount_input: str) -> GeneratorResult:
    """Convert a static QRIS into dynamic QRIS with an injected nominal amount.

    Args:
        payload: Original static QRIS string.
        amount_input: Transaction amount (e.g. 50000, '50.000', 'Rp 25.000').

    Returns:
        GeneratorResult with updated payload and recalculated CRC.
    """
    amount = normalize_amount(amount_input)
    if not amount:
        return GeneratorResult(
            success=False,
            error_message="Invalid transaction amount. Examples: 25000, 25.000, or 'Rp 50.000'",
        )

    parsed = parse_mpm(payload)
    if not parsed.is_valid:
        return GeneratorResult(
            success=False,
            error_message=f"Source QRIS payload is invalid: {parsed.error_message}",
        )

    # Cut off at last 6304 + 8 to drop any trailing characters
    last_63 = parsed.raw_data.rfind("6304")
    clean_payload = parsed.raw_data[: last_63 + 8]
    segs = _get_segments(clean_payload)
    if not segs:
        return GeneratorResult(success=False, error_message="Failed to parse top-level segments")

    if not any(s.tag == "01" for s in segs):
        return GeneratorResult(success=False, error_message="Missing Tag [01] (Point of Initiation)")

    # Filter out 54 and 63, set 01 to '12' (dynamic)
    updated: List[Segment] = []
    for s in segs:
        if s.tag in ("54", "63"):
            continue
        if s.tag == "01":
            updated.append(Segment("01", "12"))
        else:
            updated.append(s)

    # Insert Tag 54 in ascending numerical order
    insert_idx = len(updated)
    for idx, s in enumerate(updated):
        if s.tag.isdigit() and int(s.tag) > 54:
            insert_idx = idx
            break

    updated.insert(insert_idx, Segment("54", amount))
    return GeneratorResult(success=True, payload=_rebuild_payload(updated))


def to_static(payload: str) -> GeneratorResult:
    """Convert a dynamic QRIS into static QRIS by removing amount and setting Point of Initiation to 11.

    Args:
        payload: Original dynamic QRIS string.

    Returns:
        GeneratorResult with updated payload and recalculated CRC.
    """
    parsed = parse_mpm(payload)
    if not parsed.is_valid:
        return GeneratorResult(
            success=False,
            error_message=f"Source QRIS payload is invalid: {parsed.error_message}",
        )

    last_63 = parsed.raw_data.rfind("6304")
    clean_payload = parsed.raw_data[: last_63 + 8]
    segs = _get_segments(clean_payload)
    if not segs:
        return GeneratorResult(success=False, error_message="Failed to parse top-level segments")

    updated: List[Segment] = []
    for s in segs:
        if s.tag in ("54", "63"):
            continue
        if s.tag == "01":
            updated.append(Segment("01", "11"))
        else:
            updated.append(s)

    return GeneratorResult(success=True, payload=_rebuild_payload(updated))
