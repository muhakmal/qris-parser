# 🇮🇩 QRIS Parser & ASPI Validator (Python)

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Specification](https://img.shields.io/badge/Spec-ASPI%20QRIS%20v1.0-008080.svg)](https://aspi-indonesia.or.id/)
[![Standard](https://img.shields.io/badge/Standard-EMVCo%20MPM-FF6F00.svg)](https://www.emvco.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, robust Python parser and compliance validator for **Quick Response Code Indonesian Standard (QRIS)**, built strictly following the **ASPI (Asosiasi Sistem Pembayaran Indonesia) v1.0** and **EMVCo Merchant-Presented Mode (MPM)** specifications.

---

## 🌟 Key Features

- 🔍 **Full TLV (Tag-Length-Value) Parsing**: Accurately parses recursive and nested data structures (Tags 26–45 for Merchant Account Information, Tag 51 for NMID, Tag 62 for Additional Data, etc.).
- 🛡️ **CRC-16 Checksum Verification**: Validates integrity using ISO/IEC 13239 polynomial (`0x1021`, initial `0xFFFF`) to ensure QR payload integrity.
- 📋 **ASPI Business Rule Compliance Engine**:
  - Checks for mandatory root tags (Payload Format Indicator, Point of Initiation, Currency, Country, Merchant Name, City, etc.).
  - Distinguishes between **Static QR (`11`)** and **Dynamic QR (`12`)** flows (e.g. enforces National Merchant ID / NMID under Tag 51 for static QR).
  - Enforces Indonesian localization requirements (Country Code `ID` mandates postal code Tag 61).
  - Verifies currency code (`360` for Indonesian Rupiah / IDR).
  - Ensures at least one valid Merchant Account Information (MAI) block is present.
- 🎨 **Visual Tree Inspection**: Renders colorized, human-readable terminal tree structures detailing every tag, sub-tag, length, and decoded value.
- ⚡ **Dual Execution Modes**: Supports interactive CLI prompts as well as direct command-line arguments.

---

## 📸 Preview

![QRIS Parser Terminal Output](https://github.com/muhakmal/qris-parser/assets/7219902/21fd8f61-816e-4080-ac86-d78f09557641)

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Terminal supporting ANSI color codes (standard on macOS, Linux, and Windows Terminal)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/muhakmal/qris-parser.git
   cd qris-parser
   ```

2. **Create a virtual environment (recommended)**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Or install directly: `pip install colorama`)*

---

## 💻 Usage

### 1. Interactive Prompt
Run without arguments to enter interactive mode:
```bash
python app.py
```
Paste your raw QRIS string at the prompt and press `Enter`.

### 2. Direct Command-Line Argument
Pass the raw QRIS string directly as an argument:
```bash
python app.py "00020101021126580011ID.DANA.WWW011893600915302354743202100000302354743251440014ID.LINKAJA.WWW01189360091100223547430208102235475204581253033605802ID5911Kopi Kenangan6007JAKARTA61051234062070703A01630489AB"
```

---

## 📊 Supported QRIS Tag Specification (ASPI v1.0 / EMVCo)

| Tag | Name / Description | Status | Format | Notes |
|:---:|:---|:---:|:---:|:---|
| `00` | Payload Format Indicator | Mandatory | `N` (2) | Value must be `01` |
| `01` | Point of Initiation Method | Mandatory | `N` (2) | `11` = Static, `12` = Dynamic |
| `02-03` | Card Scheme Identifier | Optional | `ans` | Reserved for Visa / Mastercard |
| `26-45` | Merchant Account Information (MAI) | Conditional | Template | Domestic Acquirers / Aggregators |
| `51` | Domestic Central Repository (NMID) | Conditional | Template | Mandatory if Point of Initiation is Static (`11`) |
| `52` | Merchant Category Code (MCC) | Mandatory | `N` (4) | ISO 18245 code |
| `53` | Transaction Currency | Mandatory | `N` (3) | Standard is `360` (IDR) |
| `54` | Transaction Amount | Conditional | `ans` | Mandatory for Dynamic QR; Optional for Static |
| `55` | Tip Indicator | Optional | `N` (2) | `01` = Tip Prompt, `02` = Flat, `03` = Percentage |
| `56` | Tip Value Fixed | Conditional | `ans` | Fixed tip amount |
| `57` | Tip Value Percentage | Conditional | `ans` | Tip percentage (0.01 - 99.99%) |
| `58` | Country Code | Mandatory | `a` (2) | `ID` for Indonesia |
| `59` | Merchant Name | Mandatory | `ans` | Up to 25 characters |
| `60` | Merchant City | Mandatory | `ans` | Up to 15 characters |
| `61` | Postal Code | Conditional | `ans` | Mandatory when Country Code is `ID` |
| `62` | Additional Data Field | Optional | Template | Invoice #, Terminal ID, Reference ID |
| `63` | CRC-16 Checksum | Mandatory | `ans` (4) | ISO/IEC 13239 polynomial `0x1021` |

### Sub-Tags for Merchant Account Information (Tag 26–45 & 51)

| Sub-Tag | Field Name | Description |
|:---:|:---|:---|
| `00` | Globally Unique Identifier (GUID) | Reverse domain (e.g., `ID.CO.BANK.WWW`) |
| `01` | Merchant PAN / National Merchant ID | Acquirer Routing PAN / NMID identifier |
| `02` | Merchant ID (MID) | Internal Merchant Identification Number |
| `03` | Merchant Criteria | Merchant scale classification (UMI, UKE, UME, UBE) |

---

## 🛡️ Checksum Calculation (CRC-16 / ISO 13239)

QRIS uses an ISO/IEC 13239 CRC-16 algorithm:
- **Polynomial**: `0x1021` ($x^{16} + x^{12} + x^5 + 1$)
- **Initial Value**: `0xFFFF`
- **Data Covered**: Full QR payload up to tag `6304` (inclusive of `6304`, excluding the 4-character checksum value).

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to open an issue or submit a pull request if you want to add:
- Support for QRIS CPM (Customer-Presented Mode)
- Export to JSON / Dictionary formats
- Web-based demo or FastAPI integration

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">Made with ❤️ for the Indonesian Fintech & Developer Community by <a href="https://github.com/muhakmal">@muhakmal</a></p>
