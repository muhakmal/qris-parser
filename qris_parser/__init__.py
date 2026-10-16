"""QRIS Parser & Validator.

A Python parser, compliance auditor, and dynamic generator for Quick Response Code
Indonesian Standard (QRIS), built according to ASPI v1.0 and EMVCo MPM/CPM standards.
"""

from qris_parser.core import QRIS, format_idr
from qris_parser.cpm import check_cpm_compliance, is_cpm, parse_cpm
from qris_parser.crc import calculate_crc16, verify_crc16
from qris_parser.generator import normalize_amount, to_dynamic, to_static
from qris_parser.image import generate_qr_image
from qris_parser.lookups import lookups
from qris_parser.models import (
    BerTlv,
    ComplianceReport,
    CpmComplianceReport,
    CpmParseResult,
    GeneratorResult,
    MerchantSummary,
    ParseResult,
)
from qris_parser.mpm import parse_mpm
from qris_parser.privacy import mask_cardholder_name, mask_sensitive_value
from qris_parser.validator import check_mpm_compliance, is_valid_amount

__version__ = "0.2.0"
__all__ = [
    "QRIS",
    "parse_mpm",
    "parse_cpm",
    "is_cpm",
    "to_dynamic",
    "to_static",
    "normalize_amount",
    "generate_qr_image",
    "check_mpm_compliance",
    "check_cpm_compliance",
    "calculate_crc16",
    "verify_crc16",
    "format_idr",
    "mask_sensitive_value",
    "mask_cardholder_name",
    "is_valid_amount",
    "lookups",
    "ParseResult",
    "ComplianceReport",
    "MerchantSummary",
    "CpmParseResult",
    "CpmComplianceReport",
    "GeneratorResult",
    "BerTlv",
]
