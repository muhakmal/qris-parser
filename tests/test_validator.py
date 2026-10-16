"""Unit tests for ASPI v1.0 and EMVCo MPM compliance validator."""

from qris_parser.validator import check_mpm_compliance, is_valid_amount


def test_is_valid_amount():
    assert is_valid_amount("10000") is True
    assert is_valid_amount("10000.50") is True
    assert is_valid_amount("0.05") is True
    assert is_valid_amount("0") is False
    assert is_valid_amount("-100") is False
    assert is_valid_amount("100.123") is False  # More than 2 decimal places
    assert is_valid_amount("abc") is False


def test_validator_missing_mandatory_tags():
    report = check_mpm_compliance({})
    assert report.is_compliant is False
    assert any("[00]" in err for err in report.errors)
    assert any("[01]" in err for err in report.errors)
    assert any("[52]" in err for err in report.errors)
    assert any("[53]" in err for err in report.errors)
    assert any("[58]" in err for err in report.errors)
    assert any("[59]" in err for err in report.errors)
    assert any("[60]" in err for err in report.errors)
    assert any("[63]" in err for err in report.errors)


def test_validator_country_id_mandates_postal_code():
    tags = {
        "00": "01",
        "01": "11",
        "51": {"00": "ID.CO.QRIS.WWW", "02": "ID1020000000001", "03": "UMI"},
        "52": "5812",
        "53": "360",
        "58": "ID",
        "59": "MERCHANT",
        "60": "JAKARTA",
        "63": "ABCD",
    }
    # Missing 61
    report = check_mpm_compliance(tags)
    assert any("[61]" in err for err in report.errors)

    # Empty 61
    tags["61"] = ""
    report2 = check_mpm_compliance(tags)
    assert any("[61]" in err for err in report2.errors)


def test_validator_tip_and_convenience_fees():
    base_tags = {
        "00": "01",
        "01": "11",
        "51": {"00": "ID.CO.QRIS.WWW", "02": "ID1020000000001", "03": "UMI"},
        "52": "5812",
        "53": "360",
        "58": "ID",
        "59": "MERCHANT",
        "60": "JAKARTA",
        "61": "12345",
        "63": "ABCD",
    }

    # Case 1: Tip indicator 02 requires fixed fee (56)
    tags_02 = dict(base_tags, **{"55": "02"})
    rep_02 = check_mpm_compliance(tags_02)
    assert any("[56]" in err for err in rep_02.errors)

    # Case 2: Tip indicator 03 requires percentage fee (57)
    tags_03 = dict(base_tags, **{"55": "03"})
    rep_03 = check_mpm_compliance(tags_03)
    assert any("[57]" in err for err in rep_03.errors)

    # Case 3: Fee present without tip indicator 55
    tags_no_tip = dict(base_tags, **{"56": "5000"})
    rep_no_tip = check_mpm_compliance(tags_no_tip)
    assert any("[56]" in err for err in rep_no_tip.errors)


def test_validator_dynamic_vs_static_amount():
    base_tags = {
        "00": "01",
        "01": "12",  # Dynamic
        "51": {"00": "ID.CO.QRIS.WWW", "02": "ID1020000000001", "03": "UMI"},
        "52": "5812",
        "53": "360",
        "58": "ID",
        "59": "MERCHANT",
        "60": "JAKARTA",
        "61": "12345",
        "63": "ABCD",
    }
    # Dynamic without Tag 54 should trigger error
    rep = check_mpm_compliance(base_tags)
    assert any("[54]" in err for err in rep.errors)

    # Dynamic with Tag 54 is fine
    base_tags["54"] = "50000"
    rep2 = check_mpm_compliance(base_tags)
    assert not any("[54]" in err for err in rep2.errors)

    # Static with Tag 54 triggers warning
    base_tags["01"] = "11"
    rep3 = check_mpm_compliance(base_tags)
    assert any("[54]" in warn for warn in rep3.warnings)


def test_validator_fully_compliant():
    tags = {
        "00": "01",
        "01": "11",
        "26": {"00": "ID.DANA.WWW", "01": "936000091500000000", "02": "000000001", "03": "UMI"},
        "51": {"00": "ID.CO.QRIS.WWW", "02": "ID1020000000001", "03": "UMI"},
        "52": "5812",
        "53": "360",
        "58": "ID",
        "59": "WARUNG KOPI",
        "60": "JAKARTA",
        "61": "12345",
        "63": "ABCD",
    }
    report = check_mpm_compliance(tags)
    assert report.is_compliant is True
    assert len(report.errors) == 0
