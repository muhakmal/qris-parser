"""Unit tests for unified QRIS class and JSON formatting."""

import json

from qris_parser.core import QRIS
from tests.test_mpm import make_sample_qris


def test_qris_unified_mpm():
    sample = make_sample_qris()
    qris = QRIS.parse(sample)

    assert qris.is_valid is True
    assert qris.is_mpm is True
    assert qris.is_cpm is False
    assert qris.is_dynamic is False
    assert qris.merchant_name == "TEST SHOP"
    assert qris.city == "JAKARTA"
    assert qris.postal_code == "12340"
    assert qris.mcc == "5812"
    assert "EATING PLACES" in qris.mcc_description.upper()

    summary = qris.summary()
    assert summary.merchant_name == "TEST SHOP"
    assert summary.qris_type == "QRIS STATIC"

    json_str = qris.to_json(indent=2)
    assert "\n  " in json_str  # Verify indented JSON
    parsed_json = json.loads(json_str)
    assert parsed_json["mode"] == "MPM"
    assert parsed_json["is_valid"] is True
    assert parsed_json["summary"]["merchant_name"] == "TEST SHOP"


def test_qris_unified_cpm():
    cpm_sample = "hQVDUFYwMWGBk08HoAAABgIgIFAHUVJJU0NQTVoKk2ASNBEjRWeJn18gC1Jpa2kgRGVyaWFuXy0EaWRlbl9QF3Jpa2kuZGVyaWFuQHFyaXNjcG0uY29tnyUCeJljP590PDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MA=="
    qris = QRIS.parse(cpm_sample)

    assert qris.is_valid is True
    assert qris.is_cpm is True
    assert qris.is_mpm is False

    json_str = qris.to_json(indent=2)
    assert "\n  " in json_str
    parsed_json = json.loads(json_str)
    assert parsed_json["mode"] == "CPM"
    assert parsed_json["is_valid"] is True
