"""Unit tests for NNS, MCC lookups, and privacy masking."""

from qris_parser.lookups import lookups
from qris_parser.privacy import mask_cardholder_name, mask_sensitive_value


def test_nns_lookup():
    # 93600009 is BNI
    acquirer = lookups.get_acquirer("93600009")
    assert "Bank Negara Indonesia" in acquirer or "BNI" in acquirer

    product = lookups.get_product_name("93600009")
    assert "BNI" in product

    switchings = lookups.get_switchings("93600009")
    assert len(switchings) > 0
    assert "ArtaJasa" in switchings


def test_mcc_lookup():
    desc = lookups.get_mcc_description("5812")
    assert "EATING PLACES" in desc.upper() or "RESTAURANT" in desc.upper()

    desc_unknown = lookups.get_mcc_description("999999")
    assert desc_unknown == "Unknown Category"


def test_masking():
    # Length > 8 keeps first 4 and last 4
    masked = mask_sensitive_value("936012345678901236789")
    assert masked == "9360*************6789"

    # Length <= 4 is all asterisks
    assert mask_sensitive_value("1234") == "****"

    # Cardholder name masks except first letter
    assert mask_cardholder_name("Riki Der") == "R*******"
