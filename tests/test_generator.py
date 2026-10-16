"""Unit tests for QRIS dynamic/static generator and amount normalizer."""

from qris_parser.generator import normalize_amount, to_dynamic, to_static
from qris_parser.mpm import parse_mpm
from tests.test_mpm import make_sample_qris


def test_normalize_amount():
    assert normalize_amount("10000") == "10000"
    assert normalize_amount("10.000") == "10000"
    assert normalize_amount("Rp 25.000") == "25000"
    assert normalize_amount("rp 25.000,50") == "25000.5"
    assert normalize_amount("10000,5") == "10000.5"
    assert normalize_amount("0") is None
    assert normalize_amount("-5000") is None
    assert normalize_amount("invalid") is None


def test_to_dynamic_and_to_static():
    static_sample = make_sample_qris()
    parsed_static = parse_mpm(static_sample)
    assert parsed_static.tags["01"] == "11"
    assert "54" not in parsed_static.tags

    # Convert to Dynamic with Rp 75.000
    gen_dyn = to_dynamic(static_sample, "75.000")
    assert gen_dyn.success is True
    assert gen_dyn.payload is not None

    parsed_dyn = parse_mpm(gen_dyn.payload)
    assert parsed_dyn.is_valid is True
    assert parsed_dyn.tags["01"] == "12"
    assert parsed_dyn.tags["54"] == "75000"

    # Convert back to Static
    gen_stat = to_static(gen_dyn.payload)
    assert gen_stat.success is True
    assert gen_stat.payload is not None

    parsed_back_stat = parse_mpm(gen_stat.payload)
    assert parsed_back_stat.is_valid is True
    assert parsed_back_stat.tags["01"] == "11"
    assert "54" not in parsed_back_stat.tags
