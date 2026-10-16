"""Unit tests for MPM parser and structural diagnostics."""

from qris_parser.crc import calculate_crc16
from qris_parser.mpm import parse_mpm


def tlv(tag: str, val: str) -> str:
    return f"{tag}{len(val):02d}{val}"


def make_sample_qris() -> str:
    mai_26 = tlv("26", tlv("00", "ID.DANA.WWW") + tlv("01", "936000091500000000") + tlv("02", "000000001") + tlv("03", "UMI"))
    tag_51 = tlv("51", tlv("00", "ID.CO.QRIS.WWW") + tlv("02", "ID1020000000001") + tlv("03", "UMI"))
    body = (
        tlv("00", "01")
        + tlv("01", "11")
        + mai_26
        + tag_51
        + tlv("52", "5812")
        + tlv("53", "360")
        + tlv("58", "ID")
        + tlv("59", "TEST SHOP")
        + tlv("60", "JAKARTA")
        + tlv("61", "12340")
        + tlv("62", tlv("07", "A01"))
        + "6304"
    )
    return body + calculate_crc16(body)


def test_parse_valid_mpm():
    sample = make_sample_qris()
    res = parse_mpm(sample)
    assert res.is_valid is True
    assert res.tags["00"] == "01"
    assert res.tags["01"] == "11"
    assert res.tags["58"] == "ID"
    assert res.tags["59"] == "TEST SHOP"
    assert res.tags["60"] == "JAKARTA"
    assert isinstance(res.tags["26"], dict)
    assert res.tags["26"]["00"] == "ID.DANA.WWW"
    assert res.tags["26"]["03"] == "UMI"
    assert len(res.structural_issues) == 0


def test_parse_too_short():
    res = parse_mpm("123")
    assert res.is_valid is False
    assert "too short" in res.error_message


def test_parse_missing_crc():
    res = parse_mpm("000201010211")
    assert res.is_valid is False
    assert "CRC Tag (6304)" in res.error_message
    assert res.expected_crc is not None
    assert res.corrected_payload is not None


def test_parse_crc_mismatch():
    sample = make_sample_qris()
    bad_sample = sample[:-4] + "0000"
    res = parse_mpm(bad_sample)
    assert res.is_valid is False
    assert "CRC Mismatch" in res.error_message
    assert res.corrected_payload == sample


def test_parse_trailing_data():
    sample = make_sample_qris() + "EXTRA_GARBAGE"
    res = parse_mpm(sample)
    assert res.is_valid is True
    assert any("TRAILING DATA" in issue for issue in res.structural_issues)


def test_parse_duplicate_tags():
    # Tag 52 placed twice
    sample_prefix = tlv("00", "01") + tlv("01", "11") + tlv("52", "5812") + tlv("52", "5812") + tlv("58", "ID") + "6304"
    sample = sample_prefix + calculate_crc16(sample_prefix)
    res = parse_mpm(sample)
    assert res.is_valid is True
    assert any("DUPLICATE TAG" in issue and "[52]" in issue for issue in res.structural_issues)
