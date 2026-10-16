"""Data models and result containers for QRIS parsing and validation."""

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ParseResult:
    """Result of QRIS MPM TLV decoding and CRC validation."""

    is_valid: bool
    tags: Dict[str, Any] = field(default_factory=dict)
    raw_data: str = ""
    structural_issues: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    expected_crc: Optional[str] = None
    corrected_payload: Optional[str] = None
    partial_tags: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert result to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class ComplianceReport:
    """ASPI v1.0 and EMVCo MPM compliance evaluation report."""

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_compliant(self) -> bool:
        """True if there are zero compliance errors."""
        return len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_compliant": self.is_compliant,
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class MerchantSummary:
    """Consolidated, human-readable merchant and payment summary."""

    merchant_name: str = "-"
    city: str = "-"
    postal_code: str = "-"
    qris_type: str = "UNKNOWN"
    is_dynamic: bool = False
    mcc: str = "-"
    mcc_description: str = "-"
    currency: str = "IDR (360)"
    amount: Optional[str] = None
    amount_formatted: Optional[str] = None
    tip_or_fee: Optional[str] = None
    nmid: str = "-"
    merchant_criteria: str = "-"
    mpan: str = "-"
    mpan_masked: str = "-"
    mid: str = "-"
    terminal_label: str = "-"
    acquirer: str = "Unknown"
    product_name: str = "Unknown"
    switchings: List[str] = field(default_factory=list)
    additional_data: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class BerTlv:
    """Basic Encoding Rules (BER) TLV element for CPM."""

    tag_hex: str
    length: int
    value: bytes


@dataclass
class CpmParseResult:
    """Result of QRIS CPM (Customer-Presented Mode) decoding."""

    is_valid: bool
    tags: Dict[str, Any] = field(default_factory=dict)
    raw_binary: bytes = b""
    raw_tlvs: List[BerTlv] = field(default_factory=list)
    structural_warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        # Convert bytes to hex string for serialization
        res["raw_binary"] = self.raw_binary.hex().upper()
        res["raw_tlvs"] = [
            {"tag_hex": t.tag_hex, "length": t.length, "value_hex": t.value.hex().upper()}
            for t in self.raw_tlvs
        ]
        return res

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class CpmComplianceReport:
    """QRIS CPM compliance report."""

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_compliant(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_compliant": self.is_compliant,
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class GeneratorResult:
    """Result of QRIS transformation (e.g. static to dynamic)."""

    success: bool
    payload: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
