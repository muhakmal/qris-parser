# import re 
# import binascii 
# from colorama import Fore, Style, init 
 
# init(autoreset=True) 
 
# def calculate_crc(data: str) -> str: 
#     crc = 0xFFFF 
#     polynomial = 0x1021 
#     for byte in data: 
#         crc ^= ord(byte) << 8 
#         for _ in range(8): 
#             if crc & 0x8000: 
#                 crc = (crc << 1) ^ polynomial 
#             else: 
#                 crc = crc << 1 
#             crc &= 0xFFFF 
#     return f"{crc:04X}" 
 
# def parse_sub_tags(value: str): 
#     sub_tags = {} 
#     index = 0 
#     while index < len(value): 
#         sub_tag = value[index : index + 2] 
#         length = int(value[index + 2 : index + 4]) 
#         sub_value = value[index + 4 : index + 4 + length] 
#         sub_tags[sub_tag] = sub_value 
#         index += 4 + length 
#     return sub_tags 
 
# def parse_qris_string(qr_string: str): 
#     tags = {} 
#     index = 0 
#     try: 
#         while index < len(qr_string): 
#             tag = qr_string[index : index + 2] 
#             length = int(qr_string[index + 2 : index + 4]) 
#             value = qr_string[index + 4 : index + 4 + length] 
#             if tag in { 
#                 "26", 
#                 "27", 
#                 "28", 
#                 "29", 
#                 "30", 
#                 "31", 
#                 "32", 
#                 "33", 
#                 "34", 
#                 "35", 
#                 "36", 
#                 "37", 
#                 "38", 
#                 "39", 
#                 "40", 
#                 "41", 
#                 "42", 
#                 "43", 
#                 "44", 
#                 "45", 
#                 "62", 
#             }: 
#                 value = parse_sub_tags(value) 
#             tags[tag] = value 
#             index += 4 + length 
#     except Exception as e: 
#         return False, f"Error parsing QRIS string: {e}" 
#     data_without_crc = qr_string[:-4] 
#     provided_crc = qr_string[-4:] 
#     calculated_crc = calculate_crc(data_without_crc) 
#     if provided_crc != calculated_crc: 
#         return ( 
#             False, 
#             f"Invalid CRC. Provided: {provided_crc}, Calculated: {calculated_crc}", 
#         ) 
#     return True, tags 
 
# def validate_qris_string(qr_string: str): 
#     required_tags = ["00", "01", "26", "52", "53", "58", "59", "60", "63"] 
#     valid, result = parse_qris_string(qr_string) 
#     if not valid: 
#         return result 
#     tags = result 
#     missing_tags = [tag for tag in required_tags if tag not in tags] 
#     if missing_tags: 
#         return f"Missing required tags: {', '.join(missing_tags)}" 
#     return tags 
 
# def describe_tags(tags: dict): 
#     descriptions = { 
#         "00": "Payload Format Indicator", 
#         "01": "Point of Initiation Method", 
#         "26": "Merchant Account Information", 
#         "52": "Merchant Category Code", 
#         "51": "Merchant Account Information Domestic Central Repository", 
#         "53": "Transaction Currency", 
#         "54": "Transaction Amount", 
#         "58": "Country Code", 
#         "59": "Merchant Name", 
#         "60": "Merchant City", 
#         "61": "Postal Code", 
#         "62": "Additional Data Field Template", 
#         "63": "CRC", 
#     } 
#     sub_descriptions = { 
#         "00": "Global Unique Identifier", 
#         "01": "Merchant PAN", 
#         "02": "Merchant ID", 
#         "03": "Merchant Criteria", 
#         "05": "Reference Label", 
#         "06": "Customer Label", 
#         "07": "Terminal Label", 
#         "08": "Purpose of Transaction", 
#         "60": "Payment Label", 
#     } 
#     for tag, value in tags.items(): 
#         desc = descriptions.get(tag, "Unknown Tag") 
#         tag_color = Fore.GREEN if desc != "Unknown Tag" else Fore.RED 
#         if isinstance(value, dict): 
#             print(f"{tag_color}Tag {tag} ({desc}):") 
#             for sub_tag, sub_value in value.items(): 
#                 sub_desc = sub_descriptions.get(sub_tag, "Unknown Sub Tag") 
#                 sub_tag_color = ( 
#                     Fore.GREEN if sub_desc != "Unknown Sub Tag" else Fore.RED 
#                 ) 
#                 print(f"  {sub_tag_color}Sub Tag {sub_tag} ({sub_desc}): {sub_value}") 
#         else: 
#             print(f"{tag_color}Tag {tag} ({desc}): {value}") 

# def convert_dynamic_to_static(qr_string: str) -> str:
#     # Parse QR string and modify to static
#     valid, tags = parse_qris_string(qr_string)
#     if not valid:
#         return tags  # Return error message if parsing fails
    
#     # Set Point of Initiation Method to '11' (static)
#     tags["01"] = "11"
    
#     # Remove the transaction amount if present (Tag 54)
#     tags.pop("54", None)
    
#     # Remove any transaction-specific additional data (Tag 62)
#     if "62" in tags:
#         sub_tags = tags["62"]
#         for key in list(sub_tags.keys()):
#             if key in ["05", "06", "07", "08"]:  # Transaction-specific tags
#                 sub_tags.pop(key)
#         if not sub_tags:  # Remove Tag 62 if it becomes empty
#             tags.pop("62")
    
#     # Reconstruct the QRIS string without CRC
#     new_qr_string = ""
#     for tag, value in tags.items():
#         if isinstance(value, dict):  # Sub-tags for complex values
#             sub_tag_str = "".join(f"{sub_tag}{len(sub_value):02}{sub_value}" for sub_tag, sub_value in value.items())
#             new_qr_string += f"{tag}{len(sub_tag_str):02}{sub_tag_str}"
#         else:
#             new_qr_string += f"{tag}{len(value):02}{value}"
    
#     # Calculate and append the new CRC
#     crc = calculate_crc(new_qr_string + "63")
#     new_qr_string += f"63{len(crc):02}{crc}"
    
#     return new_qr_string

# if __name__ == "__main__": 
#     qr_string = input("Enter QRIS string: ") 
#     validation_result = validate_qris_string(qr_string) 
#     if isinstance(validation_result, dict): 
#         print("QRIS string is valid. Parsed values:") 
#         describe_tags(validation_result) 
#         # Convert to static QRIS if it is dynamic
#         static_qr_string = convert_dynamic_to_static(qr_string)
#         print("\nConverted to Static QRIS:\n", static_qr_string)
#     else: 
#         print(f"{Fore.RED}QRIS string is invalid: {validation_result}") 


import re 
import binascii 
from colorama import Fore, Style, init 
 
init(autoreset=True) 
 
def calculate_crc(data: str) -> str: 
    crc = 0xFFFF 
    polynomial = 0x1021 
    for byte in data: 
        crc ^= ord(byte) << 8 
        for _ in range(8): 
            if crc & 0x8000: 
                crc = (crc << 1) ^ polynomial 
            else: 
                crc = crc << 1 
            crc &= 0xFFFF 
    return f"{crc:04X}" 
 
def parse_sub_tags(value: str): 
    sub_tags = {} 
    index = 0 
    while index < len(value): 
        sub_tag = value[index : index + 2] 
        length = int(value[index + 2 : index + 4]) 
        sub_value = value[index + 4 : index + 4 + length] 
        sub_tags[sub_tag] = sub_value 
        index += 4 + length 
    return sub_tags 
 
def parse_qris_string(qr_string: str): 
    tags = {} 
    index = 0 
    try: 
        while index < len(qr_string): 
            tag = qr_string[index : index + 2] 
            length = int(qr_string[index + 2 : index + 4]) 
            value = qr_string[index + 4 : index + 4 + length] 
            if tag in { 
                "26", 
                "27", 
                "28", 
                "29", 
                "30", 
                "31", 
                "32", 
                "33", 
                "34", 
                "35", 
                "36", 
                "37", 
                "38", 
                "39", 
                "40", 
                "41", 
                "42", 
                "43", 
                "44", 
                "45", 
                "62", 
            }: 
                value = parse_sub_tags(value) 
            tags[tag] = value 
            index += 4 + length 
    except Exception as e: 
        return False, f"Error parsing QRIS string: {e}" 
    data_without_crc = qr_string[:-4] 
    provided_crc = qr_string[-4:] 
    calculated_crc = calculate_crc(data_without_crc) 
    if provided_crc != calculated_crc: 
        return ( 
            False, 
            f"Invalid CRC. Provided: {provided_crc}, Calculated: {calculated_crc}", 
        ) 
    return True, tags 
 
def validate_qris_string(qr_string: str): 
    required_tags = ["00", "01", "26", "52", "53", "58", "59", "60", "63"] 
    valid, result = parse_qris_string(qr_string) 
    if not valid: 
        return result 
    tags = result 
    missing_tags = [tag for tag in required_tags if tag not in tags] 
    if missing_tags: 
        return f"Missing required tags: {', '.join(missing_tags)}" 
    return tags 
 
def describe_tags(tags: dict): 
    descriptions = { 
        "00": "Payload Format Indicator", 
        "01": "Point of Initiation Method", 
        "26": "Merchant Account Information", 
        "52": "Merchant Category Code", 
        "51": "Merchant Account Information Domestic Central Repository", 
        "53": "Transaction Currency", 
        "54": "Transaction Amount", 
        "58": "Country Code", 
        "59": "Merchant Name", 
        "60": "Merchant City", 
        "61": "Postal Code", 
        "62": "Additional Data Field Template", 
        "63": "CRC", 
    } 
    sub_descriptions = { 
        "00": "Global Unique Identifier", 
        "01": "Merchant PAN", 
        "02": "Merchant ID", 
        "03": "Merchant Criteria", 
        "05": "Reference Label", 
        "06": "Customer Label", 
        "07": "Terminal Label", 
        "08": "Purpose of Transaction", 
        "60": "Payment Label", 
    } 
    for tag, value in tags.items(): 
        desc = descriptions.get(tag, "Unknown Tag") 
        tag_color = Fore.GREEN if desc != "Unknown Tag" else Fore.RED 
        if isinstance(value, dict): 
            print(f"{tag_color}Tag {tag} ({desc}):") 
            for sub_tag, sub_value in value.items(): 
                sub_desc = sub_descriptions.get(sub_tag, "Unknown Sub Tag") 
                sub_tag_color = ( 
                    Fore.GREEN if sub_desc != "Unknown Sub Tag" else Fore.RED 
                ) 
                print(f"  {sub_tag_color}Sub Tag {sub_tag} ({sub_desc}): {sub_value}") 
        else: 
            print(f"{tag_color}Tag {tag} ({desc}): {value}") 

# def convert_dynamic_to_static(qr_string: str) -> str:
#     # Parse QR string and modify to static
#     valid, tags = parse_qris_string(qr_string)
#     if not valid:
#         return tags  # Return error message if parsing fails
    
#     # Set Point of Initiation Method to '11' (static)
#     tags["01"] = "11"
    
#     # Remove the transaction amount if present (Tag 54)
#     tags.pop("54", None)
    
#     # Remove any transaction-specific additional data (Tag 62)
#     if "62" in tags:
#         sub_tags = tags["62"]
#         for key in list(sub_tags.keys()):
#             if key in ["05", "06", "07", "08"]:  # Transaction-specific tags
#                 sub_tags.pop(key)
#         if not sub_tags:  # Remove Tag 62 if it becomes empty
#             tags.pop("62")
    
#     # Reconstruct the QRIS string without CRC
#     new_qr_string = ""
#     for tag, value in tags.items():
#         if isinstance(value, dict):  # Sub-tags for complex values
#             sub_tag_str = "".join(f"{sub_tag}{len(sub_value):02}{sub_value}" for sub_tag, sub_value in value.items())
#             new_qr_string += f"{tag}{len(sub_tag_str):02}{sub_tag_str}"
#         else:
#             new_qr_string += f"{tag}{len(value):02}{value}"
    
#     # Calculate and append the new CRC
#     crc = calculate_crc(new_qr_string + "63")
#     new_qr_string += f"63{len(crc):02}{crc}"
    
#     # Revalidate the new CRC
#     valid, _ = parse_qris_string(new_qr_string)
#     if valid:
#         print(f"{Fore.GREEN}Static QRIS string generated successfully with valid CRC.")
#     else:
#         print(f"{Fore.RED}CRC validation failed for the generated Static QRIS string.")
    
#     return new_qr_string

def convert_dynamic_to_static(qr_string: str) -> str:
    # Parse QR string and modify to static
    valid, tags = parse_qris_string(qr_string)
    if not valid:
        return tags  # Return error message if parsing fails
    
    # Set Point of Initiation Method to '11' (static)
    tags["01"] = "11"
    
    # Remove the transaction amount if present (Tag 54)
    tags.pop("54", None)
    
    # Remove any transaction-specific additional data (Tag 62)
    if "62" in tags:
        sub_tags = tags["62"]
        for key in list(sub_tags.keys()):
            if key in ["05", "06", "07", "08"]:  # Transaction-specific tags
                sub_tags.pop(key)
        if not sub_tags:  # Remove Tag 62 if it becomes empty
            tags.pop("62")
    
    # Reconstruct the QRIS string without CRC
    new_qr_string = ""
    for tag, value in tags.items():
        if isinstance(value, dict):  # Sub-tags for complex values
            sub_tag_str = "".join(f"{sub_tag}{len(sub_value):02}{sub_value}" for sub_tag, sub_value in value.items())
            new_qr_string += f"{tag}{len(sub_tag_str):02}{sub_tag_str}"
        else:
            new_qr_string += f"{tag}{len(value):02}{value}"
    
    # Calculate CRC without including an actual value for the CRC field
    crc_input = new_qr_string + "6304"  # Append "63" tag with "04" as placeholder for CRC length
    crc = calculate_crc(crc_input)
    
    # Append the calculated CRC
    new_qr_string += f"6304{crc}"
    
    # Revalidate the new CRC
    valid, _ = parse_qris_string(new_qr_string)
    if valid:
        print(f"{Fore.GREEN}Static QRIS string generated successfully with valid CRC.")
    else:
        print(f"{Fore.RED}CRC validation failed for the generated Static QRIS string.")
    
    return new_qr_string


if __name__ == "__main__": 
    qr_string = input("Enter QRIS string: ") 
    validation_result = validate_qris_string(qr_string) 
    if isinstance(validation_result, dict): 
        print("QRIS string is valid. Parsed values:") 
        describe_tags(validation_result) 
        # Convert to static QRIS if it is dynamic
        static_qr_string = convert_dynamic_to_static(qr_string)
        print("\nConverted to Static QRIS:\n", static_qr_string)
    else: 
        print(f"{Fore.RED}QRIS string is invalid: {validation_result}") 
