# 🇮🇩 QRIS Parser & ASPI Validator (Python)

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Specification](https://img.shields.io/badge/Spec-ASPI%20QRIS%20v1.0-008080.svg)](https://aspi-indonesia.or.id/)
[![Standard](https://img.shields.io/badge/Standard-EMVCo%20MPM-FF6F00.svg)](https://www.emvco.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A lightweight, robust Python parser and compliance validator for **Quick Response Code Indonesian Standard (QRIS)**, built strictly following the **ASPI (Asosiasi Sistem Pembayaran Indonesia) v1.0** and **EMVCo Merchant-Presented Mode (MPM)** specifications.

---

## 🇬🇧 English

### Overview
This library decodes and validates raw QRIS payloads. It breaks down nested Tag-Length-Value (TLV) structures, verifies mathematical data integrity through ISO/IEC 13239 CRC-16 checksums, and audits strings against mandatory and conditional Indonesian regulatory payment rules.

### Key Features
- 🔍 **Full TLV (Tag-Length-Value) Parsing**: Accurately parses recursive and nested data structures (Tags 26–45 for Merchant Account Information, Tag 51 for NMID, Tag 62 for Additional Data).
- 🛡️ **CRC-16 Checksum Verification**: Validates integrity using ISO/IEC 13239 polynomial (`0x1021`, initial `0xFFFF`) to ensure payload integrity.
- 📋 **ASPI Business Rule Compliance Engine**:
  - Checks for mandatory root tags (Payload Format Indicator, Point of Initiation, Currency, Country, Merchant Name, City, etc.).
  - Distinguishes between **Static QR (`11`)** and **Dynamic QR (`12`)** flows (e.g. enforces National Merchant ID / NMID under Tag 51 for static QR).
  - Enforces Indonesian localization requirements (Country Code `ID` mandates postal code Tag 61).
  - Verifies currency code (`360` for Indonesian Rupiah / IDR).
  - Ensures at least one valid Merchant Account Information (MAI) block is present.
- 🎨 **Visual Tree Inspection**: Renders colorized, human-readable terminal tree structures detailing every tag, sub-tag, length, and decoded value.
- ⚡ **Dual Execution Modes**: Supports interactive CLI prompts as well as direct command-line arguments.

### Quickstart & Usage
```bash
# Clone & install dependencies
git clone https://github.com/muhakmal/qris-parser.git
cd qris-parser
pip install -r requirements.txt

# Mode 1: Interactive Prompt
python app.py

# Mode 2: Direct CLI Argument
python app.py "00020101021126580011ID.DANA.WWW011893600915302354743202100000302354743251440014ID.LINKAJA.WWW01189360091100223547430208102235475204581253033605802ID5911Kopi Kenangan6007JAKARTA61051234062070703A01630489AB"
```

---

## 🇮🇩 Bahasa Indonesia

### Ikhtisar
Pustaka Python ringan untuk mendekode dan memvalidasi string data **Quick Response Code Indonesian Standard (QRIS)**. Script ini membedah struktur data bertingkat Tag-Length-Value (TLV), menghitung dan memvalidasi checksum CRC-16 standar ISO/IEC 13239, serta mengaudit kepatuhan isi payload terhadap regulasi teknis pembayaran Bank Indonesia & ASPI.

### Fitur Utama
- 🔍 **Parsing TLV Rekursif & Bertingkat**: Mengurai tag bersarang seperti Merchant Account Information (Tag 26–45), NMID repositori pusat (Tag 51), dan Additional Data Field (Tag 62).
- 🛡️ **Validasi Integritas Data (CRC-16)**: Verifikasi checksum akurat menggunakan polinomial ISO/IEC 13239 (`0x1021`, initial `0xFFFF`) untuk memastikan keaslian payload QRIS.
- 📋 **Mesin Audit Kepatuhan Regulasi ASPI**:
  - Pengecekan tag wajib (Payload Indicator, Initiation Method, MCC, Currency, Merchant Name, City).
  - Validasi khusus QR Statis (`11`) vs Dinamis (`12`) (misal: Tag 51 NMID wajib pada QR Statis).
  - Validasi kode pos Tag 61 (wajib ada jika Country Code bernilai `ID`).
  - Validasi kode mata uang standar Rupiah (`360`).
  - Verifikasi ketersediaan minimal satu blok informasi rekening merchant (MAI Tag 26–45).
- 🎨 **Visualisasi Pohon Berwarna**: Tampilan hierarki data terstruktur yang rapi di terminal dengan penanda warna status (menggunakan `colorama`).
- ⚡ **Dua Mode Eksekusi**: Mode interaktif (input prompt langsung di terminal) dan mode argumen baris perintah.

### Panduan Instalasi & Penggunaan
```bash
# Clone & install dependensi
git clone https://github.com/muhakmal/qris-parser.git
cd qris-parser
pip install -r requirements.txt

# Cara 1: Mode Interaktif
python app.py

# Cara 2: Mode Argumen CLI Langsung
python app.py "<paste_string_qris_disini>"
```

---

## 📊 Tag Reference Table / Tabel Spesifikasi Tag

| Tag | Name / Nama Tag | Status | Format | Description / Deskripsi |
|:---:|:---|:---:|:---:|:---|
| `00` | Payload Format Indicator | Mandatory | `N` (2) | Nilai harus `01` |
| `01` | Point of Initiation Method | Mandatory | `N` (2) | `11` = Static, `12` = Dynamic |
| `02-03` | Card Scheme Identifier | Optional | `ans` | Reserved for Visa / Mastercard |
| `26-45` | Merchant Account Info (MAI) | Conditional | Template | Acquirer / Aggregator Domestik |
| `51` | Central Repository (NMID) | Conditional | Template | Wajib jika Point of Initiation Statis (`11`) |
| `52` | Merchant Category Code (MCC) | Mandatory | `N` (4) | Kode kategori bisnis ISO 18245 |
| `53` | Transaction Currency | Mandatory | `N` (3) | Standar `360` (IDR / Rupiah) |
| `54` | Transaction Amount | Conditional | `ans` | Nominal transaksi (wajib pada QR Dinamis) |
| `55` | Tip Indicator | Optional | `N` (2) | `01` = Prompt Tip, `02` = Flat, `03` = Persentase |
| `56` | Tip Value Fixed | Conditional | `ans` | Nilai tip tetap |
| `57` | Tip Value Percentage | Conditional | `ans` | Nilai tip persentase |
| `58` | Country Code | Mandatory | `a` (2) | `ID` untuk Indonesia |
| `59` | Merchant Name | Mandatory | `ans` | Nama merchant (maks. 25 karakter) |
| `60` | Merchant City | Mandatory | `ans` | Kota merchant (maks. 15 karakter) |
| `61` | Postal Code | Conditional | `ans` | Kode pos (wajib jika negara `ID`) |
| `62` | Additional Data Field | Optional | Template | No. invoice, Terminal ID, Reference ID |
| `63` | CRC-16 Checksum | Mandatory | `ans` (4) | Checksum integritas ISO/IEC 13239 |

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).

---
<p align="center">Made with ❤️ for the Indonesian Fintech Community by <a href="https://github.com/muhakmal">@muhakmal</a></p>
