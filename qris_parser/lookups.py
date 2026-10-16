"""Lookup tables for National Numbering System (NNS) and Merchant Category Codes (MCC)."""

import csv
from pathlib import Path
from typing import Dict, List, Optional, Set


class LookupEngine:
    """Manages loading and querying of NNS and MCC datasets."""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"
        self.data_dir = data_dir

        self._acquirer_map: Dict[str, str] = {}
        self._product_map: Dict[str, str] = {}
        self._switching_map: Dict[str, Set[str]] = {}
        self._mcc_map: Dict[str, str] = {}
        self._mcc_details: Dict[str, str] = {}

        self._is_loaded = False

    def load(self) -> None:
        """Loads CSV files into memory."""
        if self._is_loaded:
            return

        nns_path = self.data_dir / "nns_list.csv"
        if nns_path.exists():
            with open(nns_path, mode="r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f, delimiter=";")
                # Skip header
                header = next(reader, None)
                for row in reader:
                    if len(row) >= 3:
                        switching = row[0].strip()
                        nns = row[1].strip()
                        acquirer = row[2].strip()
                        product = row[3].strip() if len(row) >= 4 else ""

                        if nns:
                            self._acquirer_map[nns] = acquirer
                            if product:
                                self._product_map[nns] = product
                            if nns not in self._switching_map:
                                self._switching_map[nns] = set()
                            if switching:
                                self._switching_map[nns].add(switching)

        mcc_path = self.data_dir / "mcc_codes.csv"
        if mcc_path.exists():
            with open(mcc_path, mode="r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f, delimiter=";")
                header = next(reader, None)
                for row in reader:
                    if len(row) >= 2:
                        code = row[0].strip()
                        desc = row[1].strip()
                        detail = row[9].strip() if len(row) >= 10 else ""
                        if len(code) == 4 and code.isdigit():
                            self._mcc_map[code] = desc
                            if detail and detail != "-":
                                self._mcc_details[code] = detail

        self._is_loaded = True

    def get_acquirer(self, nns: Optional[str]) -> str:
        """Get the acquirer/issuer name for an 8-digit NNS prefix."""
        if not nns:
            return "Unknown"
        self.load()
        # Look up 8 digits
        prefix = nns[:8]
        return self._acquirer_map.get(prefix, f"Unknown Issuer ({prefix})")

    def get_product_name(self, nns: Optional[str]) -> str:
        """Get the specific product name (e.g. GoPay, DANA, BCA) for an NNS prefix."""
        if not nns:
            return "Unknown"
        self.load()
        prefix = nns[:8]
        return self._product_map.get(prefix, self.get_acquirer(nns))

    def get_switchings(self, nns: Optional[str]) -> List[str]:
        """Get switching networks (e.g. ArtaJasa, Rintis, Alto, Jalin) connected to this NNS."""
        if not nns:
            return []
        self.load()
        prefix = nns[:8]
        return sorted(list(self._switching_map.get(prefix, set())))

    def get_mcc_description(self, code: Optional[str]) -> str:
        """Get description for an ISO 18245 Merchant Category Code."""
        if not code:
            return "Unknown"
        self.load()
        return self._mcc_map.get(code, "Unknown Category")

    def get_mcc_detail(self, code: Optional[str]) -> str:
        """Get detailed definition for an MCC code."""
        if not code:
            return ""
        self.load()
        return self._mcc_details.get(code, "")


# Global singleton lookup instance
lookups = LookupEngine()
