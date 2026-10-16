"""CRC-16 (ISO/IEC 13239) implementation for QRIS and EMVCo MPM."""

from typing import Tuple, Union


def calculate_crc16(data: Union[str, bytes], encoding: str = "utf-8") -> str:
    """Calculate 16-bit CRC checksum according to ISO/IEC 13239 (EMVCo specification).

    Uses polynomial 0x1021 and initial value 0xFFFF.
    Returns a 4-character uppercase hexadecimal string.
    """
    if isinstance(data, str):
        byte_data = data.encode(encoding)
    else:
        byte_data = data

    crc = 0xFFFF
    polynomial = 0x1021

    for byte in byte_data:
        crc ^= (byte & 0xFF) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ polynomial) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF

    return f"{crc:04X}"


def verify_crc16(data_with_crc_tag: str, expected_crc: str) -> Tuple[bool, str, str]:
    """Verify CRC with support for UTF-8 and Latin-1 encodings.

    EMVCo computes CRC over payload bytes as encoded in the QR (typically UTF-8,
    though some legacy generators encode using Latin-1).

    Args:
        data_with_crc_tag: Payload up to and including '6304'.
        expected_crc: The 4-character CRC value from the payload.

    Returns:
        Tuple of (is_valid, calculated_crc_utf8, calculated_crc_latin1).
    """
    crc_utf8 = calculate_crc16(data_with_crc_tag, encoding="utf-8")
    crc_latin1 = calculate_crc16(data_with_crc_tag, encoding="latin-1")

    expected_upper = expected_crc.upper()
    is_valid = (expected_upper == crc_utf8) or (expected_upper == crc_latin1)
    return is_valid, crc_utf8, crc_latin1
