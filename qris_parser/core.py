"""High-level unified QRIS interface supporting both MPM and CPM payloads."""

import json
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from qris_parser.cpm import check_cpm_compliance, is_cpm, parse_cpm
from qris_parser.generator import to_dynamic, to_static
from qris_parser.lookups import lookups
from qris_parser.models import (
    ComplianceReport,
    CpmComplianceReport,
    CpmParseResult,
    GeneratorResult,
    MerchantSummary,
    ParseResult,
)
from qris_parser.mpm import parse_mpm
from qris_parser.privacy import mask_sensitive_value
from qris_parser.spec import ADDITIONAL_DATA_SPEC, MERCHANT_CRITERIA
from qris_parser.validator import check_mpm_compliance


def format_idr(amount_str: Optional[str]) -> Optional[str]:
    """Format numeric string into Indonesian Rupiah format (e.g. 'Rp 50.000' or 'Rp 50.000,50')."""
    if not amount_str:
        return None
    try:
        val = Decimal(amount_str.strip())
        if val == val.to_integral():
            # Format integer with dots
            formatted = f"{int(val):,}".replace(",", ".")
            return f"Rp {formatted}"
        else:
            # Format with comma decimal and dot grouping
            parts = f"{val:,.2f}".split(".")
            integer_part = parts[0].replace(",", ".")
            decimal_part = parts[1]
            return f"Rp {integer_part},{decimal_part}"
    except Exception:
        return f"Rp {amount_str}"


class QRIS:
    """Unified representation of a QRIS payload (Merchant or Customer mode)."""

    def __init__(
        self,
        raw_payload: str,
        is_cpm_mode: bool,
        mpm_result: Optional[ParseResult] = None,
        cpm_result: Optional[CpmParseResult] = None,
    ):
        self.raw_payload = raw_payload
        self.is_cpm = is_cpm_mode
        self.is_mpm = not is_cpm_mode
        self._mpm = mpm_result
        self._cpm = cpm_result

    @classmethod
    def parse(cls, payload: str) -> "QRIS":
        """Parse raw QRIS payload, automatically detecting MPM or CPM."""
        stripped = payload.strip()
        if is_cpm(stripped):
            cpm_res = parse_cpm(stripped)
            return cls(raw_payload=stripped, is_cpm_mode=True, cpm_result=cpm_res)
        else:
            mpm_res = parse_mpm(stripped)
            return cls(raw_payload=stripped, is_cpm_mode=False, mpm_result=mpm_res)

    @property
    def is_valid(self) -> bool:
        """True if the payload format and CRC are structurally valid."""
        if self.is_cpm:
            return self._cpm.is_valid if self._cpm else False
        return self._mpm.is_valid if self._mpm else False

    @property
    def error_message(self) -> Optional[str]:
        if self.is_cpm and self._cpm:
            return self._cpm.error_message
        if self._mpm:
            return self._mpm.error_message
        return None

    @property
    def tags(self) -> Dict[str, Any]:
        """Dictionary of decoded tags."""
        if self.is_cpm and self._cpm:
            return self._cpm.tags
        if self._mpm:
            return self._mpm.tags
        return {}

    @property
    def is_dynamic(self) -> bool:
        """True if Point of Initiation (Tag 01) is '12' (Dynamic)."""
        if self.is_mpm:
            return self.tags.get("01") == "12"
        return False

    @property
    def merchant_name(self) -> str:
        if self.is_mpm:
            return str(self.tags.get("59", "-"))
        return "-"

    @property
    def city(self) -> str:
        if self.is_mpm:
            return str(self.tags.get("60", "-"))
        return "-"

    @property
    def postal_code(self) -> str:
        if self.is_mpm:
            return str(self.tags.get("61", "-"))
        return "-"

    @property
    def amount(self) -> Optional[str]:
        if self.is_mpm:
            val = self.tags.get("54")
            return str(val) if val is not None else None
        return None

    @property
    def amount_formatted(self) -> Optional[str]:
        return format_idr(self.amount)

    @property
    def mcc(self) -> str:
        if self.is_mpm:
            return str(self.tags.get("52", "-"))
        return "-"

    @property
    def mcc_description(self) -> str:
        if self.mcc and self.mcc != "-":
            return lookups.get_mcc_description(self.mcc)
        return "-"

    @property
    def nmid(self) -> str:
        if self.is_mpm:
            tag51 = self.tags.get("51")
            if isinstance(tag51, dict):
                return str(tag51.get("02", "-"))
            if isinstance(tag51, str) and tag51.startswith("ID"):
                return tag51
        return "-"

    @property
    def mpan(self) -> str:
        """Extract first Merchant PAN from MAI templates."""
        if self.is_mpm:
            for k in range(26, 46):
                mai = self.tags.get(str(k))
                if isinstance(mai, dict) and "01" in mai:
                    return str(mai["01"])
        return "-"

    @property
    def mpan_masked(self) -> str:
        pan = self.mpan
        return mask_sensitive_value(pan) if pan != "-" else "-"

    @property
    def acquirer(self) -> str:
        pan = self.mpan
        if pan != "-" and len(pan) >= 8:
            return lookups.get_acquirer(pan[:8])
        return "Unknown"

    @property
    def product_name(self) -> str:
        pan = self.mpan
        if pan != "-" and len(pan) >= 8:
            return lookups.get_product_name(pan[:8])
        return "Unknown"

    @property
    def switchings(self) -> List[str]:
        pan = self.mpan
        if pan != "-" and len(pan) >= 8:
            return lookups.get_switchings(pan[:8])
        return []

    def summary(self) -> MerchantSummary:
        """Generate a complete MerchantSummary object."""
        poi = self.tags.get("01")
        qris_type = "QRIS STATIC" if poi == "11" else ("QRIS DYNAMIC" if poi == "12" else f"UNKNOWN ({poi})")

        # Criteria
        crit_code = None
        tag51 = self.tags.get("51")
        if isinstance(tag51, dict):
            crit_code = tag51.get("03")
        if not crit_code:
            for k in range(26, 46):
                mai = self.tags.get(str(k))
                if isinstance(mai, dict) and "03" in mai:
                    crit_code = mai["03"]
                    break

        crit_desc = MERCHANT_CRITERIA.get(str(crit_code), str(crit_code)) if crit_code else "-"

        # Mid & Terminal Label
        mid = "-"
        for k in range(26, 46):
            mai = self.tags.get(str(k))
            if isinstance(mai, dict) and "02" in mai:
                mid = str(mai["02"])
                break

        tag62 = self.tags.get("62")
        terminal = "-"
        add_data: List[Dict[str, str]] = []
        if isinstance(tag62, dict):
            terminal = str(tag62.get("07", "-"))
            for sk, sv in sorted(tag62.items()):
                add_data.append({"tag": sk, "name": ADDITIONAL_DATA_SPEC.get(sk, "Sub Data"), "value": str(sv)})

        # Tip or Fee
        tip_indicator = self.tags.get("55")
        tip_or_fee: Optional[str] = None
        if tip_indicator == "01":
            tip_or_fee = "Prompted Tip (Customer Defined)"
        elif tip_indicator == "02":
            fee = self.tags.get("56", "")
            tip_or_fee = f"Fixed Fee: {format_idr(str(fee))}"
        elif tip_indicator == "03":
            pct = self.tags.get("57", "")
            tip_or_fee = f"Percentage Fee: {pct}%"

        return MerchantSummary(
            merchant_name=self.merchant_name,
            city=self.city,
            postal_code=self.postal_code,
            qris_type=qris_type,
            is_dynamic=self.is_dynamic,
            mcc=self.mcc,
            mcc_description=self.mcc_description,
            currency=f"IDR (360)" if self.tags.get("53") == "360" else str(self.tags.get("53", "-")),
            amount=self.amount,
            amount_formatted=self.amount_formatted,
            tip_or_fee=tip_or_fee,
            nmid=self.nmid,
            merchant_criteria=crit_desc,
            mpan=self.mpan,
            mpan_masked=self.mpan_masked,
            mid=mid,
            terminal_label=terminal,
            acquirer=self.acquirer,
            product_name=self.product_name,
            switchings=self.switchings,
            additional_data=add_data,
        )

    def check_compliance(self) -> Union[ComplianceReport, CpmComplianceReport]:
        """Audit regulatory compliance against ASPI specs."""
        if self.is_cpm:
            return check_cpm_compliance(self.tags)
        if self._mpm:
            return check_mpm_compliance(self._mpm)
        return check_mpm_compliance(self.tags)

    def to_dynamic(self, amount: str) -> GeneratorResult:
        """Convert static QRIS to dynamic QRIS with amount."""
        return to_dynamic(self.raw_payload, amount)

    def to_static(self) -> GeneratorResult:
        """Convert dynamic QRIS to static QRIS."""
        return to_static(self.raw_payload)

    def to_dict(self) -> Dict[str, Any]:
        """Export summary, tags, and validation status to dictionary."""
        return {
            "mode": "CPM" if self.is_cpm else "MPM",
            "is_valid": self.is_valid,
            "error_message": self.error_message,
            "summary": self.summary().to_dict() if self.is_mpm and self.is_valid else None,
            "tags": self.tags,
            "raw_payload": self.raw_payload,
        }

    def to_json(self, indent: int = 2) -> str:
        """Export to indented JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
