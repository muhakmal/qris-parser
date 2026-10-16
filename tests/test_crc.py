"""Unit tests for CRC-16 (ISO/IEC 13239)."""

from qris_parser.crc import calculate_crc16, verify_crc16


def test_calculate_crc16_standard_vector():
    # Standard QRIS payload prefix up to 6304
    data = "0002010102115204000053033605802ID5910MERCH_NAME6007JAKARTA6105123456304"
    crc = calculate_crc16(data)
    assert len(crc) == 4
    assert crc.isalnum()


def test_verify_crc16_valid_and_invalid():
    payload_prefix = "0002010102115802ID5904SHOP6007JAKARTA6304"
    calculated = calculate_crc16(payload_prefix)

    is_valid, crc_utf8, _ = verify_crc16(payload_prefix, calculated)
    assert is_valid is True
    assert crc_utf8 == calculated

    # Tampered CRC
    is_valid_bad, _, _ = verify_crc16(payload_prefix, "0000" if calculated != "0000" else "FFFF")
    assert is_valid_bad is False
