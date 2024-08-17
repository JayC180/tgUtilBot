import magic
import os
import json
from virus_total_scan import virus_scan, get_scan_results
config_file = json.load(open("config.json"))
allowed_extensions = config_file["allowedExtensions"]
max_size = 50 * 1024 * 1024 # 50 mb

def is_extension_allowed(filename: str) -> bool:
    if('.' in filename):
        return filename.split('.', 1)[-1].lower() in allowed_extensions
    return False

def is_file_size_allowed(file_size: int) -> bool:
    return file_size <= max_size

def is_mime_type_allowed(file_path: str) -> bool:
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    return mime_type.split('/')[1] in allowed_extensions

def validate_file(file_path: str, filename: str, file_type: str, file_size: int) -> str:
    if(file_type == "document"):
        if not is_extension_allowed(filename):
            return f"Invalid file extension. filename: {filename}"

    if not is_file_size_allowed(file_size):
        return "File size exceeds the maximum allowed limit."

    if not is_mime_type_allowed(file_path):
        return "Invalid MIME type."
    
    # virustotal scan
    analysis_id = virus_scan(file_path)
    if analysis_id.startswith("Error"):
        return analysis_id

    scan_result = get_scan_results(analysis_id)
    if "malicious" in scan_result:
        print(scan_result)
        return "File malicious"

    return "File is valid."
