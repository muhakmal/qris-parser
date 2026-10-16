"""Specifications and dictionaries for QRIS (ASPI v1.0 / EMVCo MPM) and QRIS CPM."""

from typing import Dict, Optional, Set

# Root-level specification for QRIS MPM
ROOT_SPEC: Dict[str, Dict[str, str]] = {
    "00": {"desc": "Payload Format Indicator", "status": "M", "val": "01"},
    "01": {"desc": "Point of Initiation Method", "status": "M"},  # 11=Static, 12=Dynamic
    "02": {"desc": "Merchant Account Info (Visa)", "status": "O"},
    "03": {"desc": "Merchant Account Info (Visa)", "status": "O"},
    "04": {"desc": "Merchant Account Info (Mastercard)", "status": "O"},
    "05": {"desc": "Merchant Account Info (Mastercard)", "status": "O"},
    "26": {"desc": "Merchant Account Info (Domestic)", "status": "C"},
    "51": {"desc": "Domestic Central Repository (NMID)", "status": "C"},
    "52": {"desc": "Merchant Category Code (MCC)", "status": "M"},
    "53": {"desc": "Transaction Currency", "status": "M", "val": "360"},
    "54": {"desc": "Transaction Amount", "status": "C"},
    "55": {"desc": "Tip or Convenience Fee Indicator", "status": "O"},
    "56": {"desc": "Value of Convenience Fee (Fixed)", "status": "C"},
    "57": {"desc": "Value of Convenience Fee (%)", "status": "C"},
    "58": {"desc": "Country Code", "status": "M", "val": "ID"},
    "59": {"desc": "Merchant Name", "status": "M"},
    "60": {"desc": "Merchant City", "status": "M"},
    "61": {"desc": "Postal Code", "status": "O"},  # Mandatory when Country=ID
    "62": {"desc": "Additional Data Field", "status": "O"},
    "63": {"desc": "CRC", "status": "M"},
    "64": {"desc": "Merchant Information - Language Template", "status": "O"},
}

# Merchant Account Information Sub-tags (26-45 and 51)
MAI_SPEC: Dict[str, Dict[str, str]] = {
    "00": {"desc": "Globally Unique Identifier", "status": "M"},
    "01": {"desc": "Merchant PAN (MPAN)", "status": "M"},
    "02": {"desc": "Merchant ID", "status": "M"},
    "03": {"desc": "Merchant Criteria", "status": "M"},
}

# Central Repository Sub-tags (Tag 51)
DOMESTIC_REPOSITORY_SPEC: Dict[str, str] = {
    "00": "Globally Unique Identifier",
    "02": "National Merchant ID (NMID)",
    "03": "Merchant Criteria",
}

# Tag 62 Additional Data Sub-tags
ADDITIONAL_DATA_SPEC: Dict[str, str] = {
    "01": "Bill Number",
    "02": "Mobile Number",
    "03": "Store Label",
    "04": "Loyalty Number",
    "05": "Reference Label",
    "06": "Customer Label",
    "07": "Terminal Label",
    "08": "Purpose of Transaction",
    "09": "Additional Consumer Data Request",
}

# Tag 64 Language Template Sub-tags
LANGUAGE_TEMPLATE_SPEC: Dict[str, str] = {
    "00": "Language Preference",
    "01": "Merchant Name (Alternate Language)",
    "02": "Merchant City (Alternate Language)",
}

# Merchant Criteria mapping
MERCHANT_CRITERIA: Dict[str, str] = {
    "UMI": "Usaha Mikro",
    "UKE": "Usaha Kecil",
    "UME": "Usaha Menengah",
    "UBE": "Usaha Besar",
    "URE": "Usaha Reguler",
}

# Maximum lengths according to EMVCo MPM & ASPI
TAG_MAX_LENGTHS: Dict[str, int] = {
    "00": 2,
    "01": 2,
    "52": 4,
    "53": 3,
    "54": 13,
    "55": 2,
    "56": 13,
    "57": 5,
    "58": 2,
    "59": 25,
    "60": 15,
    "61": 10,
    "63": 4,
}

# CPM Tag descriptions (Spesifikasi QRIS CPM v0.3)
CPM_TAG_DESCRIPTIONS: Dict[str, str] = {
    "85": "Payload Format Indicator (CPV01)",
    "61": "Application Template",
    "4F": "ADF Name (AID)",
    "50": "Application Label",
    "57": "Track 2 Equivalent Data",
    "5A": "Application PAN",
    "5F20": "Cardholder Name",
    "5F2D": "Language Preference",
    "5F50": "Issuer URL",
    "9F08": "Application Version Number",
    "9F25": "Last 4 Digits of PAN",
    "9F19": "Token Requestor ID",
    "9F24": "Payment Account Reference (PAR)",
    "9F76": "Additional Information",
    "63": "Application Specific Transparent Template",
    "9F74": "Issuer QRIS Data",
    "9F7A": "Issuer Public Key Certificate (IPKC)",
    "9F7B": "Issuer QRIS Data Encrypted",
    "9F26": "Application Cryptogram (AC)",
    "9F27": "Cryptogram Information Data (CID)",
    "9F10": "Issuer Application Data (IAD)",
    "9F36": "Application Transaction Counter (ATC)",
    "82": "Application Interchange Profile (AIP)",
    "9F37": "Unpredictable Number (UN)",
}

# Binary/BCD Tags in CPM that should be represented in hexadecimal
CPM_BINARY_TAGS: Set[str] = {
    "4F", "57", "5A", "82", "9F08", "9F10", "9F19", "9F25", "9F26", "9F27",
    "9F36", "9F37", "9F74", "9F7A", "9F7B",
}


def is_template_tag(tag: str, parent_tag: Optional[str] = None) -> bool:
    """Check if a tag's value is itself a TLV template."""
    if not tag.isdigit():
        return False
    tag_int = int(tag)
    if parent_tag is None:
        return (26 <= tag_int <= 51) or tag_int == 62 or tag_int == 64 or (80 <= tag_int <= 99)
    if parent_tag == "62":
        return 50 <= tag_int <= 99
    return False


def get_root_name(tag: str) -> str:
    """Return descriptive name for a root-level tag."""
    if tag in ROOT_SPEC:
        return ROOT_SPEC[tag]["desc"]
    if tag.isdigit():
        tag_int = int(tag)
        if 2 <= tag_int <= 3:
            return "Merchant Account Info (Visa)"
        if 4 <= tag_int <= 5:
            return "Merchant Account Info (Mastercard)"
        if 6 <= tag_int <= 8:
            return "Merchant Account Info (EMVCo)"
        if 9 <= tag_int <= 10:
            return "Merchant Account Info (Discover)"
        if 11 <= tag_int <= 12:
            return "Merchant Account Info (Amex)"
        if 13 <= tag_int <= 14:
            return "Merchant Account Info (JCB)"
        if 15 <= tag_int <= 16:
            return "Merchant Account Info (UnionPay)"
        if 17 <= tag_int <= 25:
            return "Merchant Account Info (EMVCo reserved)"
        if 26 <= tag_int <= 45:
            return "Merchant Account Info (Domestic)"
        if 46 <= tag_int <= 50:
            return "Merchant Account Info (Reserved)"
        if 65 <= tag_int <= 79:
            return "RFU for EMVCo"
        if 80 <= tag_int <= 99:
            return "Unreserved Template"
    return "Proprietary"


def get_subtag_name(parent_tag: str, subtag: str) -> str:
    """Return descriptive name for a sub-tag within a template tag."""
    if parent_tag == "62":
        if subtag in ADDITIONAL_DATA_SPEC:
            return ADDITIONAL_DATA_SPEC[subtag]
        if subtag.isdigit():
            sub_int = int(subtag)
            if 10 <= sub_int <= 49:
                return "RFU for EMVCo"
            if 50 <= sub_int <= 99:
                return "Payment System Specific Template"
        return "Unknown Additional Data"
    if parent_tag == "64":
        return LANGUAGE_TEMPLATE_SPEC.get(subtag, "RFU for EMVCo")
    if parent_tag == "51":
        return DOMESTIC_REPOSITORY_SPEC.get(subtag, "Payment Network Specific")
    if parent_tag.isdigit() and 26 <= int(parent_tag) <= 45:
        if subtag in MAI_SPEC:
            return MAI_SPEC[subtag]["desc"]
        return "Payment Network Specific"
    if subtag == "00":
        return "Globally Unique Identifier"
    return "Payment Network Specific"
