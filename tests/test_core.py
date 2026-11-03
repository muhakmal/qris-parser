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


# MotionPay-printed sticker carrying four acquirers (OVO, BCA, Mandiri, MotionPay).
MULTI_ACQUIRER_QRIS = (
    "00020101021126620010ID.OVO.WWW011893600912000122956002155ar0Kv0D8WcMJto0303UKE"
    "27650013ID.CO.BCA.WWW011893600014000196168902150008850019616890303UMI"
    "28690021ID.CO.BANKMANDIRI.WWW01189360000801955257670211719552576790303UMI"
    "29670016ID.MOTIONPAY.WWW01189360081600001202920214131430001202920303UMI"
    "51440014ID.CO.QRIS.WWW0215ID10211043464520303UKE5204581253033605802ID"
    "5911Dapur Ceria6013Jakarta Utara61051445062070703A016304023D"
)


def test_summary_lists_every_acquirer():
    summary = QRIS.parse(MULTI_ACQUIRER_QRIS).summary()

    assert [a.tag for a in summary.acquirers] == ["26", "27", "28", "29"]
    assert [a.nns for a in summary.acquirers] == ["93600912", "93600014", "93600008", "93600816"]
    assert summary.acquirers[0].product_name == "OVO"
    assert summary.acquirers[3].acquirer == "PT MNC Teknologi Nusantara"
    assert summary.acquirers[3].global_id == "ID.MOTIONPAY.WWW"
    # The first MAI is still the headline acquirer, for backward compatibility.
    assert summary.acquirer == "PT Visionet Internasional"


def test_payment_routing_explains_on_us_off_us_and_criteria():
    notes = QRIS.parse(MULTI_ACQUIRER_QRIS).summary().payment_routing

    assert any("Paid with MotionPay: on-us" in n for n in notes)
    assert any("off-us" in n and "tag 26 (OVO)" in n for n in notes)
    assert any("split across 4 acquirers" in n for n in notes)
    assert any("criteria differ" in n and "tag 51 = UKE" in n for n in notes)


def test_payment_routing_single_acquirer():
    notes = QRIS.parse(make_sample_qris()).summary().payment_routing

    assert len(notes) == 1
    assert notes[0].startswith("Every payment")
