import sys
from colorama import Fore, Style, init

init(autoreset=True)

# ==========================================
# 1. REFERENSI SPESIFIKASI (ASPI V1.0)
# ==========================================

# Format: ID: {Deskripsi, Status_Default (M/O/C), Format (N/ans/S)}
# [cite_start]Ref: Tabel 3.6 [cite: 1034-1040]
ROOT_SPEC = {
    "00": {"desc": "Payload Format Indicator", "status": "M", "val": "01"},
    "01": {"desc": "Point of Initiation Method", "status": "M"}, # 11=Static, 12=Dynamic
    "02": {"desc": "Merchant Account Info (VISA)", "status": "O"},
    "26": {"desc": "Merchant Account Info (DOMESTIC)", "status": "C"}, # Minimal 1 MAI wajib
    "51": {"desc": "Domestic Central Repository (NMID)", "status": "C"}, # Wajib jika Static
    "52": {"desc": "Merchant Category Code (MCC)", "status": "M", "len": 4},
    "53": {"desc": "Transaction Currency", "status": "M", "val": "360"}, # 360 = IDR
    "54": {"desc": "Transaction Amount", "status": "C"},
    "55": {"desc": "Tip Indicator", "status": "O"},
    "56": {"desc": "Tip Value Fixed", "status": "C"},
    "57": {"desc": "Tip Value Percentage", "status": "C"},
    "58": {"desc": "Country Code", "status": "M", "val": "ID"},
    "59": {"desc": "Merchant Name", "status": "M"},
    "60": {"desc": "Merchant City", "status": "M"},
    "61": {"desc": "Postal Code", "status": "O"}, # Jadi M jika Country=ID
    "62": {"desc": "Additional Data Field", "status": "O"},
    "63": {"desc": "CRC", "status": "M", "len": 4}
}

# Ref: Tabel 4.3
MAI_SPEC = {
    "00": {"desc": "Global Unique Identifier", "status": "M"},
    "01": {"desc": "Merchant PAN", "status": "M"},
    "02": {"desc": "Merchant ID", "status": "M"},
    "03": {"desc": "Merchant Criteria", "status": "M"}
}

# ==========================================
# 2. CORE PARSER & CRC
# ==========================================

def calculate_crc(data: str) -> str:
    """ISO/IEC 13239 CRC Calculation"""
    crc = 0xFFFF
    polynomial = 0x1021
    # Encode latin-1 untuk memastikan byte processing benar
    for byte in data.encode('latin-1'):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ polynomial
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"

def parse_tlv(value: str):
    tags = {}
    index = 0
    while index < len(value):
        try:
            # Safety check parsing
            if index + 4 > len(value): break
            
            tag = value[index : index + 2]
            len_str = value[index + 2 : index + 4]
            
            if not len_str.isdigit(): break
            length = int(len_str)
            
            if index + 4 + length > len(value): break
            
            sub_val = value[index + 4 : index + 4 + length]
            tags[tag] = sub_val
            index += 4 + length
        except: break
    return tags

def parse_root(qr_string: str):
    tags = {}
    index = 0
    
    # Validasi Dasar
    if len(qr_string) < 4: return False, "String terlalu pendek"
    
    try:
        while index < len(qr_string):
            # Cek sisa string cukup untuk header (4 char)
            if index + 4 > len(qr_string): break
            
            tag = qr_string[index : index + 2]
            len_str = qr_string[index + 2 : index + 4]
            
            if not len_str.isdigit(): return False, f"Length Header Invalid di index {index+2}"
            length = int(len_str)
            
            val_start = index + 4
            val_end = val_start + length
            
            if val_end > len(qr_string):
                return False, f"Tag {tag} declare length {length} tapi sisa string kurang"
                
            value = qr_string[val_start : val_end]
            
            # Recursive Parse untuk Template (MAI 26-45, 51, 62)
            is_template = False
            if tag.isdigit():
                itag = int(tag)
                if (26 <= itag <= 45) or itag == 51 or itag == 62 or itag == 64:
                    is_template = True
            
            if is_template:
                tags[tag] = parse_tlv(value)
            else:
                tags[tag] = value
                
            index = val_end
            
    except Exception as e: return False, str(e)
    
    # Validasi CRC Checksum
    # Ref: CRC dihitung dari semua data KECUALI value CRC itu sendiri
    if not qr_string.endswith("6304" + qr_string[-4:].upper()):
        # Coba cari CRC manual jika ada sampah whitespace
        last_63 = qr_string.rfind("6304")
        if last_63 == -1: return False, "CRC Tag (63) Missing/Invalid"
        data_calc = qr_string[:last_63+4]
        crc_provided = qr_string[last_63+4:]
    else:
        data_calc = qr_string[:-4]
        crc_provided = qr_string[-4:]
        
    crc_calc = calculate_crc(data_calc)
    if crc_provided.upper() != crc_calc.upper():
        return False, f"CRC Mismatch! Input: {crc_provided}, Calc: {crc_calc}"
        
    return True, tags

# ==========================================
# 3. VALIDASI ATURAN INDONESIA (ASPI)
# ==========================================

def check_compliance(tags):
    errors = []
    warnings = []

    # 1. Cek Mandatory Tags Dasar (Missing Check)
    for tag_id, spec in ROOT_SPEC.items():
        if spec['status'] == 'M' and tag_id not in tags:
            # Kecuali Tag 61 & 51 yg kondisional, nanti dicek terpisah
            if tag_id not in ['61', '51']: 
                errors.append(f"MISSING MANDATORY TAG: [{tag_id}] {spec['desc']}")

    # 2. Validasi Khusus Tag 58 (Country) & 61 (Postal)
    # [cite_start]Ref: Tabel 3.6 Note [cite: 1040]
    country = tags.get('58', '')
    if country == 'ID':
        if '61' not in tags:
            errors.append(f"MISSING MANDATORY TAG: [61] Postal Code (Wajib karena Country=ID)")
        elif not tags['61']: # Ada tapi kosong
            errors.append(f"INVALID VALUE: [61] Postal Code tidak boleh kosong")

    # 3. Validasi Tag 60 (City) - Tidak Boleh Kosong
    if '60' in tags:
        if len(tags['60']) == 0:
            errors.append(f"INVALID VALUE: [60] Merchant City length 0 (Wajib diisi)")
    
    # 4. Validasi Tag 51 (NMID) vs Tag 01 (Static/Dynamic)
    # [cite_start]Ref: 4.7.7 [cite: 407-408]
    poi = tags.get('01', '')
    if poi == '11': # Static
        if '51' not in tags:
            errors.append(f"MISSING MANDATORY TAG: [51] Domestic Repo/NMID (Wajib untuk QR Static)")
    
    # 5. Validasi Minimal 1 Merchant Account (26-45)
    # Ref: Tabel 3.6
    has_mai = any(k for k in tags if k.isdigit() and 26 <= int(k) <= 45)
    if not has_mai and '51' not in tags:
        errors.append("MISSING MAI: Minimal harus ada satu Merchant Account Info (Tag 26-45 atau 51)")

    # 6. Validasi Currency IDR
    if '53' in tags and tags['53'] != '360':
        warnings.append(f"WARNING CURRENCY: Tag 53 bernilai {tags['53']}, standar IDR adalah 360")

    return errors, warnings

# ==========================================
# 4. TAMPILAN VISUAL
# ==========================================

def print_tree(tags, level=0):
    indent = "   " * level
    for k in sorted(tags.keys()):
        v = tags[k]
        
        # Determine Desc
        desc = "Unknown"
        if level == 0: 
            desc = ROOT_SPEC.get(k, {}).get('desc', 'Proprietary')
            if k.isdigit() and 26 <= int(k) <= 45: desc = "Merchant Account Info"
        elif level == 1:
            desc = MAI_SPEC.get(k, {}).get('desc', 'Sub Data')
            
        # Coloring
        key_color = Fore.CYAN if level == 0 else Fore.YELLOW
        
        if isinstance(v, dict):
            print(f"{indent}{key_color}[{k}]{Style.RESET_ALL} {desc}:")
            print_tree(v, level + 1)
        else:
            # Cek Empty Value Error visual
            val_display = v
            if v == "": 
                val_display = f"{Fore.RED}<EMPTY STRING>{Style.RESET_ALL}"
            print(f"{indent}{key_color}[{k}]{Style.RESET_ALL} {desc}: {val_display}")

# ==========================================
# 5. MAIN EXECUTION (INTERACTIVE)
# ==========================================

if __name__ == "__main__":
    print(f"{Style.BRIGHT}=== QRIS VALIDATOR (ASPI SPEC V1.0) ==={Style.RESET_ALL}")
    
    raw_input = ""

    # Cek apakah user memberikan argumen saat menjalankan script
    if len(sys.argv) > 1:
        raw_input = sys.argv[1]
    else:
        # JIKA TIDAK ADA ARGUMEN, MINTA INPUT DARI USER DI TERMINAL
        print(f"\n{Fore.YELLOW}Silakan paste string QRIS Anda di bawah ini dan tekan Enter:{Style.RESET_ALL}")
        try:
            raw_input = input("> ").strip() # .strip() membuang spasi/newline di awal/akhir
        except KeyboardInterrupt:
            print("\nOperasi dibatalkan.")
            sys.exit()

    if not raw_input:
        print(f"{Fore.RED}Error: Input tidak boleh kosong.{Style.RESET_ALL}")
        sys.exit()

    print(f"\n{Fore.BLUE}Analyzing String:{Style.RESET_ALL} {raw_input[:30]}...")
    
    # 1. Parse & CRC
    is_valid, result = parse_root(raw_input)
    
    if not is_valid:
        print(f"\n{Fore.RED}❌ PARSING FAILED:{Style.RESET_ALL} {result}")
    else:
        tags = result
        print(f"\n{Fore.GREEN}✅ FORMAT & CRC VALID{Style.RESET_ALL}")
        
        # 2. Tampilkan Struktur Data
        print(f"\n{Style.BRIGHT}--- DATA STRUCTURE ---{Style.RESET_ALL}")
        print_tree(tags)
        
        # 3. Validasi Bisnis (Mandatory/Conditional)
        errors, warnings = check_compliance(tags)
        
        print(f"\n{Style.BRIGHT}--- COMPLIANCE REPORT ---{Style.RESET_ALL}")
        if not errors and not warnings:
            print(f"{Fore.GREEN}PERFECT! QRIS Sesuai Standar ASPI.{Style.RESET_ALL}")
        else:
            for err in errors:
                print(f"❌ {Fore.RED}{err}{Style.RESET_ALL}")
            for warn in warnings:
                print(f"⚠️ {Fore.YELLOW}{warn}{Style.RESET_ALL}")