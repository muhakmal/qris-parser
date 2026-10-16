# 🇮🇩 QRIS Parser & Validator (Python)

[![CI](https://github.com/muhakmal/qris-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/muhakmal/qris-parser/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/qris-parser.svg)](https://pypi.org/project/qris-parser/)
[![BaskomLabs Showcase](https://img.shields.io/badge/Showcase-baskom.fun%2Fopen--source-00d1b2.svg)](https://baskom.fun/open-source)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Specification](https://img.shields.io/badge/Spec-ASPI%20QRIS%20v1.0%20%7C%20CPM%20v0.3-008080.svg)](https://aspi-indonesia.or.id/)
[![Standard](https://img.shields.io/badge/Standard-EMVCo%20MPM%20%26%20CPM-FF6F00.svg)](https://www.emvco.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

Production-grade Python library, compliance auditor, dynamic generator, and CLI tool for **Quick Response Code Indonesian Standard (QRIS)**, built strictly following **Bank Indonesia**, **ASPI (Asosiasi Sistem Pembayaran Indonesia) v1.0**, and **EMVCo MPM & CPM** standards.

---

## 🇬🇧 English

### Overview
**QRIS Parser** is an all-in-one developer toolkit for decoding, validating, modifying, and inspecting QRIS payment payloads. It supports both **Merchant-Presented Mode (MPM)** and **Customer-Presented Mode (CPM)**, verifies data integrity with ISO/IEC 13239 CRC-16 checksums, audits regulatory business rules, resolves National Numbering System (NNS) acquirers/issuers, and converts static QR codes to dynamic QR codes with automatic nominal injection.

### ✨ Key Features
- 🔍 **Full TLV & BER-TLV Parsing**:
  - **MPM (Merchant-Presented Mode)**: Recursively parses nested TLV structures (Tags 26–45 for Merchant Account Information, Tag 51 for NMID, Tag 62 for Additional Data, Tag 64 for Language Template).
  - **CPM (Customer-Presented Mode)**: Decodes Base64 BER-TLV payloads (`CPV01`), application templates (`Tag 61`), ADF names, PAN, cardholder names, and cryptograms.
- 🛡️ **ISO/IEC 13239 CRC-16 Engine**: Calculates and validates CRC-16 checksums (`0x1021`, initial `0xFFFF`) with dual-charset support (UTF-8 with Latin-1 fallback) and automated CRC repair suggestions.
- 📋 **ASPI Business Rule Compliance Auditor**:
  - Validates mandatory root tags, character length limits, and tag ordering (Tag `00` first, Tag `63` last).
  - Distinguishes **Static QR (`11`)** vs. **Dynamic QR (`12`)** flows (e.g. enforces National Merchant ID / NMID on static QR, validates nominal presence on dynamic QR).
  - Enforces Indonesian localization requirements (Country Code `ID` mandates postal code Tag `61`).
  - Audits Tip & Convenience Fee combinations (Tags `55`, `56`, `57`).
  - Detects duplicate tags and trailing data bytes.
- 🔄 **QRIS Dynamic Generator & Converter**:
  - Converts Static QRIS to Dynamic QRIS by injecting transaction amounts (Tag `54`) and recomputing CRC checksums.
  - Smart Rupiah amount normalizer (accepts `10000`, `10.000`, `Rp 25.000,50`).
- 🏦 **Built-in NNS & MCC Lookups**:
  - Built-in database of 100+ Indonesian banks & e-wallets (BCA, Mandiri, BRI, BNI, DANA, GoPay, OVO, ShopeePay, LinkAja, Nobu, etc.) and switching networks (ArtaJasa, Rintis, Alto, Jalin) from 8-digit NNS prefixes.
  - Comprehensive ISO 18245 Merchant Category Code (MCC) dictionary with merchant types and details.
- 🔒 **Data Privacy & Redaction**: Built-in masking helpers for sensitive MPAN and cardholder data.
- 📦 **Dual Interface**: Use as a Python library in your application or as a standalone terminal CLI (`qris-parser`).

---

### 📦 Installation

#### Using `pip` Package Manager

From GitHub repository directly:
```bash
pip install git+https://github.com/muhakmal/qris-parser.git
```

From local directory (development mode):
```bash
git clone https://github.com/muhakmal/qris-parser.git
cd qris-parser
pip install -e .
```

*Note: Once published to PyPI, you can simply run `pip install qris-parser`.*

---

### 🚀 Python Library Usage

#### 1. Parsing & Validating MPM QRIS
```python
from qris_parser import QRIS

# Raw QRIS string
payload = "00020101021126570011ID.DANA.WWW011893600009150000000002090000000010303UMI51440014ID.CO.QRIS.WWW0215ID10200000000010303UMI5204581253033605802ID5909TEST SHOP6007JAKARTA61051234062070703A0163048827"

# Parse QRIS (auto-detects MPM or CPM)
qris = QRIS.parse(payload)

print("Valid CRC:", qris.is_valid)
print("Merchant Name:", qris.merchant_name)
print("Type:", "Dynamic" if qris.is_dynamic else "Static")
print("Acquirer:", qris.acquirer)          # e.g., "PT Bank Negara Indonesia (Persero), Tbk (BNI Mobile Banking)"
print("Switchings:", qris.switchings)      # e.g., ["ArtaJasa"]
print("MCC:", qris.mcc_description)        # e.g., "EATING PLACES & RESTAURANTS"

# Check ASPI compliance
compliance = qris.check_compliance()
if compliance.is_compliant:
    print("✅ Fully compliant with ASPI v1.0 specifications")
else:
    print("❌ Compliance Errors:", compliance.errors)

# Export formatted indented JSON
print(qris.to_json(indent=2))
```

#### 2. Convert Static QRIS to Dynamic QRIS (Add Amount)
```python
from qris_parser import QRISGenerator

static_qris = "00020101021126570011ID.DANA.WWW011893600009150000000002090000000010303UMI51440014ID.CO.QRIS.WWW0215ID10200000000010303UMI5204581253033605802ID5909TEST SHOP6007JAKARTA61051234062070703A0163048827"

# Inject amount Rp 50.000 (normalizer accepts "50000", "50.000", or "Rp 50.000")
result = QRISGenerator.to_dynamic(static_qris, "50000")

if result.success:
    print("Dynamic QRIS Payload:", result.payload)
else:
    print("Error:", result.error_message)
```

#### 3. Parsing Customer-Presented Mode (CPM) QRIS
```python
from qris_parser import QRISCpmParser

# Base64-encoded CPM payload (starts with hQVDUFY)
cpm_payload = "hQVDUFYwMWGBk08HoAAABgIgIFAHUVJJU0NQTVoKk2ASNBEjRWeJn18gC1Jpa2kgRGVyaWFuXy0EaWRlbl9QF3Jpa2kuZGVyaWFuQHFyaXNjcG0uY29tnyUCeJljP590PDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MA=="

cpm = QRISCpmParser.parse(cpm_payload)
if cpm.is_valid:
    print("Application Label:", cpm.tags.get("61", {}).get("50"))  # "QRISCPM"
    print("Cardholder Name:", cpm.tags.get("61", {}).get("5F20"))
```

#### 4. Exporting QR Code Image (PNG)
```python
# Requires optional dependency: pip install "qris-parser[image]"
qris.save_image("qris_invoice.png")
```

---

### 💻 CLI Usage

Once installed, use the `qris-parser` command line interface:

```bash
# 1. Interactive terminal mode
qris-parser

# 2. Inspect a payload directly
qris-parser "000201010211..."

# 3. Output clean, formatted JSON
qris-parser "000201010211..." --json

# 4. Generate dynamic QRIS with nominal
qris-parser "000201010211..." --to-dynamic "75000"

# 5. Render and save QRIS as a PNG image
qris-parser "000201010211..." --save-image invoice.png

# 6. Show merchant summary and issuer lookup
qris-parser "000201010211..." --summary

# 7. Validate ASPI compliance only (exit code 0 on pass, 1 on fail)
qris-parser "000201010211..." --validate
```

---

## 🇮🇩 Bahasa Indonesia

### Ikhtisar
**QRIS Parser** adalah toolkit Python lengkap untuk mendekode, mengaudit kepatuhan, memodifikasi, dan memeriksa string pembayaran QRIS. Mendukung mode pembayaran **Merchant-Presented Mode (MPM / QR Toko)** maupun **Customer-Presented Mode (CPM / QR Pembeli di Ponsel)**, validasi integritas checksum ISO/IEC 13239 CRC-16, audit aturan ASPI v1.0 & Bank Indonesia, identifikasi bank/e-wallet acquirer lewat National Numbering System (NNS), serta generator nominal QRIS statis ke dinamis.

### ✨ Fitur Utama
- 🔍 **Parsing TLV & BER-TLV Lengkap**:
  - **MPM (QR Toko)**: Mengurai struktur bertingkat (Tag 26–45 MAI, Tag 51 NMID, Tag 62 Additional Data, Tag 64 Bahasa).
  - **CPM (QR Ponsel Konsumen)**: Dekode payload Base64 BER-TLV (`CPV01`), Application Template (`Tag 61`), AID, PAN, dan Cardholder Name.
- 🛡️ **Mesin CRC-16 ISO/IEC 13239**: Checksum akurat (`0x1021`, initial `0xFFFF`) dengan dukungan multi-encoding (UTF-8 dan Latin-1 fallback) serta rekomendasi auto-repair payload jika CRC rusak.
- 📋 **Audit Regulasi & Kepatuhan ASPI v1.0**:
  - Validasi tag wajib, batasan panjang karakter, dan urutan tag (Tag `00` wajib pertama, Tag `63` wajib terakhir).
  - Deteksi QR Statis (`11`) vs Dinamis (`12`) (misal: Tag 51 NMID wajib di QR Statis, Tag 54 nominal wajib di QR Dinamis).
  - Penegakan regulasi wilayah Indonesia (Country Code `ID` mewajibkan kode pos Tag `61`).
  - Aturan Tip dan Convenience Fee (Tag `55`, `56`, `57`).
  - Deteksi duplikasi tag dan trailing data tak terduga.
- 🔄 **QRIS Dynamic Generator & Converter**:
  - Mengubah QRIS Statis menjadi Dinamis dengan menyuntikkan nominal transaksi (Tag `54`) dan menghitung ulang checksum CRC-16 secara instan.
  - Normalisasi nominal Rupiah yang pintar (bisa input `10000`, `10.000`, atau `Rp 25.000,50`).
- 🏦 **Database Lookup NNS & MCC Terintegrasi**:
  - Mengenali 100+ bank & e-wallet Indonesia (BCA, Mandiri, BRI, BNI, DANA, GoPay, OVO, ShopeePay, LinkAja, dll.) dan switching (ArtaJasa, Rintis, Alto, Jalin) dari 8-digit NNS.
  - Database lengkap kode kategori bisnis MCC ISO 18245 beserta penjelasannya.
- 🔒 **Privasi & Masking**: Fungsi bawaan untuk menyamarkan nomor rekening/PAN dan nama nasabah.
- 📦 **Fleksibilitas Penggunaan**: Dapat di-import sebagai library Python atau dijalankan langsung di terminal via perintah `qris-parser`.

---

### 📦 Panduan Instalasi & Package Manager

Install langsung dari repositori GitHub:
```bash
pip install git+https://github.com/muhakmal/qris-parser.git
```

Atau clone untuk pengembangan lokal:
```bash
git clone https://github.com/muhakmal/qris-parser.git
cd qris-parser
pip install -e .
```

---

## 📊 Tabel Spesifikasi Tag QRIS MPM (ASPI / EMVCo)

| Tag | Nama / Deskripsi Tag | Status | Format | Keterangan Aturan |
|:---:|:---|:---:|:---:|:---|
| `00` | Payload Format Indicator | Mandatory | `N` (2) | Harus selalu bernilai `01` dan berada di urutan pertama |
| `01` | Point of Initiation Method | Mandatory | `N` (2) | `11` = QR Statis, `12` = QR Dinamis |
| `02-03` | Card Scheme Identifier | Optional | `ans` | Skema kartu internasional (Visa / Mastercard) |
| `26-45` | Merchant Account Info (MAI) | Conditional | Template | Rekening Acquirer / Domestik (minimal ada 1 jika tanpa Tag 51) |
| `51` | Central Repository (NMID) | Conditional | Template | Wajib jika Point of Initiation Statis (`11`) |
| `52` | Merchant Category Code (MCC) | Mandatory | `N` (4) | 4 digit kode kategori bisnis ISO 18245 |
| `53` | Transaction Currency | Mandatory | `N` (3) | Standar QRIS domestik: `360` (IDR / Rupiah) |
| `54` | Transaction Amount | Conditional | `ans` (maks. 13) | Nominal transaksi (wajib pada QR Dinamis `12`) |
| `55` | Tip / Convenience Fee Indicator | Optional | `N` (2) | `01` = Prompt Tip, `02` = Fixed Fee, `03` = Percentage Fee |
| `56` | Value of Convenience Fee (Fixed) | Conditional | `ans` (maks. 13) | Nilai fee flat (wajib jika `55=02`) |
| `57` | Value of Convenience Fee (%) | Conditional | `ans` (maks. 5) | Persentase fee 0–100% (wajib jika `55=03`) |
| `58` | Country Code | Mandatory | `a` (2) | `ID` untuk QRIS Indonesia |
| `59` | Merchant Name | Mandatory | `ans` (maks. 25) | Nama merchant / toko |
| `60` | Merchant City | Mandatory | `ans` (maks. 15) | Kota lokasi merchant |
| `61` | Postal Code | Conditional | `ans` (maks. 10) | Kode pos (wajib jika negara `ID`) |
| `62` | Additional Data Field | Optional | Template | No. referensi, Terminal ID, Invoice |
| `63` | CRC-16 Checksum | Mandatory | `ans` (4) | Checksum integritas ISO/IEC 13239, wajib di akhir string |
| `64` | Merchant Information Language | Optional | Template | Nama dan kota alternatif (ISO 639) |

---

## 🤝 Contributing
Kontribusi sangat terbuka! Silakan baca panduan lengkap di [CONTRIBUTING.md](CONTRIBUTING.md).

1. Fork repo ini & buat branch fitur: `git checkout -b feat/nama-fitur`.
2. Jalankan unit test: `pytest`.
3. Buat Pull Request dengan penjelasan yang jelas.

---

## 📄 License
Project ini dilisensikan di bawah [MIT License](LICENSE). Bebas digunakan untuk keperluan komersial, open source, maupun edukasi.

---
<p align="center">Part of the <a href="https://baskom.fun/open-source">BaskomLabs Open Source Initiative</a> · Made with ❤️ by <a href="https://github.com/muhakmal">@muhakmal</a></p>
