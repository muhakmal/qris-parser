import sys
from colorama import Fore, Style, init

init(autoreset=True)

# --- REFERENSI SPESIFIKASI (Sama seperti sebelumnya) ---
# [cite: 282, 380, 294, 285]

ROOT_TAGS = {
    "00": "Payload Format Indicator", "01": "Point of Initiation Method", 
    "52": "Merchant Category Code", "53": "Transaction Currency", 
    "54": "Transaction Amount", "58": "Country Code", 
    "59": "Merchant Name", "60": "Merchant City", 
    "61": "Postal Code", "63": "CRC",
    "51": "Domestic Central Repository"
}

# --- DEBUGGING UTILITIES ---

def log_debug(message, level="INFO"):
    if level == "INFO":
        print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} {message}")
    elif level == "SUCCESS":
        print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} {message}")
    elif level == "ERROR":
        print(f"{Fore.RED}[FAIL]{Style.RESET_ALL} {message}")
    elif level == "WARN":
        print(f"{Fore.YELLOW}[WARN]{Style.RESET_ALL} {message}")

def visualize_error(qr_string, index, error_msg):
    print(f"\n{Fore.RED}=== PARSING STOPPED AT INDEX {index} ==={Style.RESET_ALL}")
    
    # Tampilkan konteks sekitar error (10 char sebelum dan sesudah)
    start = max(0, index - 15)
    end = min(len(qr_string), index + 15)
    
    snippet = qr_string[start:end]
    pointer = " " * (index - start) + "^ ERROR HERE"
    
    print(f"String Context:  ...{snippet}...")
    print(f"Visual Pointer:     {Fore.RED}{pointer}{Style.RESET_ALL}")
    print(f"Reason: {error_msg}\n")

# --- CORE LOGIC ---

def calculate_crc_debug(data: str) -> str:
    # CRC Calculation mengacu pada ISO/IEC 13239 [cite: 476]
    # Polynomial '1021' (hex) dan initial value 'FFFF' (hex) [cite: 476]
    crc = 0xFFFF
    polynomial = 0x1021
    for byte in data.encode('latin-1'):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ polynomial
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"

def parse_tlv_debug(value, indent_level=0):
    tags = {}
    index = 0
    indent = "  " * indent_level
    
    log_debug(f"{indent}Start parsing Sub-Tags (Length: {len(value)})")
    
    while index < len(value):
        # 1. Cek sisa panjang string untuk ID
        if index + 2 > len(value):
            log_debug(f"{indent}Sisa string tidak cukup untuk mengambil ID Tag.", "WARN")
            break
            
        tag = value[index : index + 2]
        
        # 2. Cek sisa panjang string untuk Length
        if index + 4 > len(value):
            log_debug(f"{indent}Tag {tag} ditemukan, tapi string habis sebelum Length header.", "WARN")
            break
            
        length_str = value[index + 2 : index + 4]
        
        if not length_str.isdigit():
            log_debug(f"{indent}Tag {tag}: Format Length '{length_str}' bukan angka.", "ERROR")
            break
            
        length = int(length_str)
        
        # 3. Cek sisa panjang string untuk Value
        if index + 4 + length > len(value):
            actual_len = len(value) - (index + 4)
            log_debug(f"{indent}Tag {tag}: Length header {length}, tapi sisa data cuma {actual_len}.", "ERROR")
            break
            
        sub_value = value[index + 4 : index + 4 + length]
        tags[tag] = sub_value
        log_debug(f"{indent}├─ SubTag [{tag}] Len:{length} Val:{sub_value}", "SUCCESS")
        
        index += 4 + length
        
    return tags

def parse_qris_deep_debug(qr_string):
    tags = {}
    index = 0
    
    print(f"\n{Style.BRIGHT}--- STEP 1: PARSING STRUCTURE ---{Style.RESET_ALL}")
    
    if len(qr_string) < 4:
        visualize_error(qr_string, 0, "String terlalu pendek (< 4 chars).")
        return tags

    while index < len(qr_string):
        # --- HEADER ANALYSIS ---
        # Format: ID (2 digit) + Length (2 digit) + Value (Var)
        # Ref: [cite: 254, 342]
        
        # 1. Ambil ID
        if index + 2 > len(qr_string):
            visualize_error(qr_string, index, "End of string reached while expecting Tag ID.")
            break
        tag = qr_string[index : index + 2]
        
        # 2. Ambil Length Header
        if index + 4 > len(qr_string):
            visualize_error(qr_string, index, f"Tag {tag} found, but missing Length Header.")
            break
        length_str = qr_string[index + 2 : index + 4]
        
        # Validasi Format Length
        if not length_str.isdigit():
            visualize_error(qr_string, index+2, f"Length Header '{length_str}' is not numeric.")
            break
        length = int(length_str)
        
        # 3. Ambil Value
        value_start_index = index + 4
        value_end_index = value_start_index + length
        
        if value_end_index > len(qr_string):
            visualize_error(qr_string, value_start_index, 
                            f"Tag {tag} expects {length} chars, but only {len(qr_string) - value_start_index} remain.")
            break
            
        value = qr_string[value_start_index : value_end_index]
        
        # LOGGING
        tag_name = ROOT_TAGS.get(tag, "Unknown/Proprietary")
        log_debug(f"Index {index}: Found Tag [{tag}] ({tag_name}) -> Length: {length}")
        
        # RECURSIVE PARSING (TEMPLATE)
        # Ref: Tag 26-45 (Merchant Info), 51 (Domestic), 62 (Additional Data) [cite: 388, 290]
        parsed_value = value
        if (tag.isdigit() and 26 <= int(tag) <= 45) or tag in ["51", "62", "64"]:
            log_debug(f"  -> Detected Template Tag [{tag}], attempting deep parse...")
            parsed_value = parse_tlv_debug(value, indent_level=1)
        
        tags[tag] = parsed_value
        
        # Move Index
        index = value_end_index

    return tags

def validate_crc_deep(qr_string, tags):
    print(f"\n{Style.BRIGHT}--- STEP 2: CRC INTEGRITY CHECK ---{Style.RESET_ALL}")
    
    # CRC harus berada di Tag 63 dan merupakan objek terakhir [cite: 272, 475]
    if "63" not in tags:
        log_debug("Tag 63 (CRC) tidak ditemukan dalam hasil parsing.", "ERROR")
        return

    # Check posisi Tag 63 di raw string
    # Kita cari '6304' terakhir di string
    crc_marker = "6304"
    last_occurrence = qr_string.rfind(crc_marker)
    
    if last_occurrence == -1:
         log_debug("Header Tag CRC '6304' tidak ditemukan di raw string.", "ERROR")
         return
         
    # Pastikan itu benar-benar di akhir string (allow whitespace trim issue)
    if last_occurrence + 8 != len(qr_string):
        log_debug(f"Posisi Tag 63 aneh. Ditemukan di index {last_occurrence}, tapi panjang string {len(qr_string)}.", "WARN")
        log_debug("Standar mengharuskan CRC menjadi urutan terakhir data object[cite: 360].", "WARN")

    # Ambil data input untuk kalkulasi (Semua string KECUALI Value dari CRC)
    # Ref: "Data yang dihitung adalah seluruh data object termasuk ID, panjang karakter, Value, serta ID dan Panjang karakter dari CRC sendiri" 
    data_to_calculate = qr_string[:last_occurrence + 4] 
    provided_crc = qr_string[last_occurrence + 4:]
    
    calculated_crc = calculate_crc_debug(data_to_calculate)
    
    print(f"Data Input CRC : {data_to_calculate[:20]}...{data_to_calculate[-10:]} (Total {len(data_to_calculate)} chars)")
    print(f"Provided CRC   : {Fore.YELLOW}{provided_crc}{Style.RESET_ALL}")
    print(f"Calculated CRC : {Fore.CYAN}{calculated_crc}{Style.RESET_ALL}")
    
    if provided_crc.upper() == calculated_crc.upper():
        log_debug("CRC MATCH! Data Integrity Verified.", "SUCCESS")
    else:
        log_debug("CRC MISMATCH! Data mungkin korup atau terpotong.", "ERROR")

def show_results(tags):
    print(f"\n{Style.BRIGHT}--- STEP 3: PARSED DATA DUMP ---{Style.RESET_ALL}")
    if not tags:
        print("No tags were successfully parsed.")
        return

    for k, v in tags.items():
        desc = ROOT_TAGS.get(k, "Unknown")
        if isinstance(v, dict):
            print(f"[{k}] {desc}:")
            for sk, sv in v.items():
                print(f"    └─ [{sk}] : {sv}")
        else:
            print(f"[{k}] {desc} : {v}")

if __name__ == "__main__":
    print(f"{Style.BRIGHT}{Fore.CYAN}=== QRIS DEEP DEBUGGER TOOL ==={Style.RESET_ALL}")
    print("Paste string QRIS anda (bahkan yang invalid/terpotong):")
    
    if len(sys.argv) > 1:
        raw_qris = sys.argv[1]
    else:
        raw_qris = input("> ").strip()
    
    # 1. Jalankan Parsing dengan toleransi error
    parsed_tags = parse_qris_deep_debug(raw_qris)
    
    # 2. Tampilkan hasil yang BERHASIL dibaca sejauh ini
    show_results(parsed_tags)
    
    # 3. Cek CRC (hanya jika minimal ada data)
    if len(raw_qris) > 4:
        validate_crc_deep(raw_qris, parsed_tags)