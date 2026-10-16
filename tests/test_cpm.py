"""Unit tests for Customer-Presented Mode (CPM) parsing and compliance."""

from qris_parser.cpm import check_cpm_compliance, is_cpm, parse_cpm


def test_is_cpm():
    cpm_sample = "hQVDUFYwMWGBk08HoAAABgIgIFAHUVJJU0NQTVoKk2ASNBEjRWeJn18gC1Jpa2kgRGVyaWFuXy0EaWRlbl9QF3Jpa2kuZGVyaWFuQHFyaXNjcG0uY29tnyUCeJljP590PDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MA=="
    assert is_cpm(cpm_sample) is True
    assert is_cpm("000201010211") is False


def test_parse_cpm_sample():
    cpm_sample = "hQVDUFYwMWGBk08HoAAABgIgIFAHUVJJU0NQTVoKk2ASNBEjRWeJn18gC1Jpa2kgRGVyaWFuXy0EaWRlbl9QF3Jpa2kuZGVyaWFuQHFyaXNjcG0uY29tnyUCeJljP590PDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MA=="
    result = parse_cpm(cpm_sample)
    assert result.is_valid is True
    assert result.tags["85"] == "CPV01"

    app_template = result.tags.get("61")
    assert isinstance(app_template, dict)
    assert app_template["50"] == "QRISCPM"
    assert app_template["4F"] == "A0000006022020"

    # Cardholder name tag 5F20
    assert "5F20" in app_template
    assert "Riki Derian" in app_template["5F20"]

    # Check compliance
    rep = check_cpm_compliance(result.tags)
    assert rep.is_compliant is True
    assert len(rep.errors) == 0
    # Warning has masked name
    assert any("Cardholder Name" in w and "R*******" in w for w in rep.warnings)
