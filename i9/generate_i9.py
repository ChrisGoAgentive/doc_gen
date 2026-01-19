import sys
import os
import argparse
import fitz  # PyMuPDF: pip install pymupdf
import random
from datetime import datetime, timedelta

# Ensure we can import from utils in the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import util placeholders if specific ones aren't available in this context, 
# otherwise rely on the ones you have.
try:
    from utils.data_utils import DataLoader, DataFormatter
    from utils.signature_utils import SignatureGenerator
except ImportError:
    # Minimal fallback if utils aren't in path for this specific run
    class DataLoader:
        @staticmethod
        def load(path):
            import json
            with open(path, 'r') as f: return json.load(f)
    class SignatureGenerator:
        pass # Handle separately

# Configure the font path for signatures
DEFAULT_FONT_PATH = os.path.join("fonts", "PlaywriteIN-VariableFont_wght.ttf")

# --- CONFIGURATION ---
# UPDATED: Now points to the compliance data file by default
DEFAULT_INPUT_JSON = "data/i9_compliance_data.json"
DEFAULT_TEMPLATE_PDF = "templates/fi-9_flat.pdf"
DEFAULT_OUTPUT_DIR = "output/eligibility"

# ==============================================================================
#  STEP 1: COORDINATE FIELD MAPPING
#  Format: [Page Index, X, Y, Font Size, Max Width]
# ==============================================================================
I9_COORD_MAP = {
    # --- Page 1: Employee Information ---
    "last_name":        [0, 45, 183, 10, 150], 
    "first_name":       [0, 205, 183, 10, 130],
    "middle_initial":   [0, 345, 183, 10, 30],
    "other_last_names": [0, 425, 183, 10, 130],
    
    "address":          [0, 45, 210, 10, 180],
    "apt_number":       [0, 235, 210, 10, 50],
    "city":             [0, 305, 210, 10, 130],
    "state":            [0, 465, 210, 10, 40],
    "zip_code":         [0, 510, 210, 10, 60],
    
    "dob":              [0, 45, 237, 10, 80],
    "ssn":              [0, 152, 237, 10, 100],
    "email":            [0, 265, 237, 10, 180],
    "phone":            [0, 455, 237, 10, 110],

    # Citizenship Checkboxes (Coordinates are examples, verify with your specific PDF)
    "citizen_check":    [0, 182, 268, 12, 20], # "X" mark
    
    # Signature Section
    "emp_signature":    [0, 45, 370, 12, 250], # Signature font
    "sign_date":        [0, 370, 370, 10, 100],

    "emp_last_name_top": [0, 45, 108, 10, 150],
    "emp_first_name_top": [0, 205, 108, 10, 130],
    "citizenship_stat":  [0, 350, 108, 10, 30], # "1" for citizen

    # --- SECTION 2: DOCUMENT VERIFICATION ---
    # List A
    # User provided relative coordinates, mapped to Page 2 (Index 1)
    "list_a_doc_title":     [0, 130, 448, 10, 100],
    "list_a_issuing_auth":  [0, 130, 465, 10, 100],
    "list_a_doc_number":    [0, 130, 483, 10, 100],
    "list_a_doc_exp":       [0, 130, 500, 10, 100],

    # List B
    "list_b_doc_title":     [1, 280, 448, 10, 100],
    "list_b_issuing_auth":  [1, 280, 465, 10, 100],
    "list_b_doc_number":    [1, 280, 483, 10, 100],
    "list_b_doc_exp":       [1, 280, 500, 10, 100],

    # List C
    "list_c_doc_title":     [0, 425, 448, 10, 100],
    "list_c_issuing_auth":  [0, 425, 465, 10, 100],
    "list_c_doc_number":    [0, 425, 483, 10, 100],
    "list_c_doc_exp":       [0, 425, 500, 10, 100],

    # Certification
    "first_day_employment": [0, 460, 677, 10, 100],

    "employer_name":        [0, 45, 710, 10, 100],
    "signature_employer":   [0, 290, 710, 12, 200], # Increased size for sig
    "employer_sig_date":    [0, 488, 710, 10, 100],
    "business_name":        [0, 45, 735, 10, 100],
    "business_address":     [0, 255, 735, 10, 100],
}

def format_date_us(date_str):
    """
    Helper to convert YYYY-MM-DD to MM/DD/YYYY.
    Returns original string if parsing fails or if already formatted.
    """
    if not date_str:
        return ""
    try:
        # Try YYYY-MM-DD
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%m/%d/%Y")
    except ValueError:
        return date_str

def fill_i9_pdf(record, template_path, output_path, font_path=None):
    """
    Fills the I-9 PDF using PyMuPDF (fitz) with coordinate-based text insertion.
    """
    try:
        doc = fitz.open(template_path)
    except Exception as e:
        print(f"Error opening template {template_path}: {e}")
        return False

    # --- MAP JSON DATA TO I-9 FIELDS ---
    # We construct a dictionary 'data' that matches the keys in I9_COORD_MAP
    # pulling values from the 'record' (JSON)
    
    # 1. Parse Name
    fname = record.get("first_name", "")
    lname = record.get("last_name", "")
    
    # 2. Parse Address
    full_address = record.get("address", "")
    # Simple heuristic to split "Street, City, State Zip"
    addr_parts = full_address.split(',')
    street = addr_parts[0].strip() if len(addr_parts) > 0 else ""
    city = addr_parts[1].strip() if len(addr_parts) > 1 else ""
    state_zip = addr_parts[2].strip() if len(addr_parts) > 2 else ""
    state = state_zip.split(' ')[0] if state_zip else ""
    zip_code = state_zip.split(' ')[1] if len(state_zip.split(' ')) > 1 else ""

    # 3. Dates
    # Use formatted sign_date from compliance data if available, else hire_date
    sign_date_str = record.get("employer_sig_date_user", record.get("hire_date", ""))
    sign_date_str = format_date_us(sign_date_str) # Ensure MM/DD/YYYY

    dob_str = format_date_us(record.get("dob", "")) # Ensure MM/DD/YYYY for DOB

    data = {
        # Page 1
        "last_name": lname,
        "first_name": fname,
        "middle_initial": record.get("middle_initial", "N/A"),
        "other_last_names": record.get("other_last_names", "N/A"),
        "address": street,
        "apt_number": record.get("apt_number", ""),
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "dob": dob_str,
        "ssn": record.get("ssn", "").replace("-", " "), # Replace hyphens with spaces for better spacing
        "email": record.get("email", ""),
        "phone": record.get("phone", ""),
        
        "citizen_check": record.get("citizen_check", ""),
        "emp_signature": f"{fname} {lname}", # Stylized font
        "sign_date": sign_date_str,

        # Page 2
        "emp_last_name_top": lname,
        "emp_first_name_top": fname,
        "citizenship_stat": record.get("citizenship_stat", ""),
        
        # Section 2 - Compliance Data Mapped to PDF Keys
        "list_a_doc_title":     record.get("list_a_doc_title_user", ""),
        "list_a_issuing_auth":  record.get("list_a_issuing_auth_user", ""),
        "list_a_doc_number":    record.get("list_a_doc_number_user", ""),
        "list_a_doc_exp":       format_date_us(record.get("list_a_doc_exp_user", "")),

        "list_b_doc_title":     record.get("list_b_doc_title_user", ""),
        "list_b_issuing_auth":  record.get("list_b_issuing_auth_user", ""),
        "list_b_doc_number":    record.get("list_b_doc_number_user", ""),
        "list_b_doc_exp":       format_date_us(record.get("list_b_doc_exp_user", "")),

        "list_c_doc_title":     record.get("list_c_doc_title_user", ""),
        "list_c_issuing_auth":  record.get("list_c_issuing_auth_user", ""),
        "list_c_doc_number":    record.get("list_c_doc_number_user", ""),
        "list_c_doc_exp":       format_date_us(record.get("list_c_doc_exp_user", "")),

        "first_day_employment": format_date_us(record.get("first_day_employment_user", "")),

        "employer_name":        f"{record.get('rep_first_name', '')} {record.get('rep_last_name', '')}",
        "signature_employer":   record.get("signature_employer_user", ""),
        "employer_sig_date":    record.get("employer_sig_date_user", ""),
        "business_name":        record.get("business_name_user", ""),
        "business_address":     record.get("business_address_user", ""),
    }

    # --- RENDER TEXT ONTO PDF ---
    for key, val in data.items():
        if key in I9_COORD_MAP and val:
            coords = I9_COORD_MAP[key]
            page_idx = coords[0]
            x, y = coords[1], coords[2]
            font_size = coords[3]
            
            # Select page
            if page_idx < len(doc):
                page = doc[page_idx]
                
                # Check for SSN to apply manual character spacing
                if key == "ssn":
                    # For SSN, we assume 'val' is formatted like "XXX XX XXXX" or "XXX-XX-XXXX"
                    # We will draw each character with a fixed width offset
                    clean_ssn = val.replace("-", "").replace(" ", "")
                    # Standard I-9 SSN Box geometry: 
                    # 3 digits, space, 2 digits, space, 4 digits
                    
                    # Manual offsets based on typical I-9 box spacing
                    # Start X is provided in coord map (135)
                    # We iterate and push X forward
                    
                    current_x = x
                    char_spacing = 11.5 # Tuning parameter for box width
                    
                    # Logic: Draw first 3, skip gap, draw next 2, skip gap, draw last 4
                    for i, char in enumerate(clean_ssn):
                        page.insert_text((current_x, y), str(char), fontsize=font_size, fontname="Helv")
                        
                        # Add spacing
                        current_x += char_spacing


                # Choose Font
                elif "signature" in key and font_path and os.path.exists(font_path):
                    # Insert stylized text for signatures if font exists
                    page.insert_text((x, y), str(val), fontsize=font_size+2, fontname="Helv", color=(0, 0, 0.5))
                elif "check" in key:
                     page.insert_text((x, y), str(val), fontsize=font_size, fontname="Helv", color=(0, 0, 0))
                else:
                    page.insert_text((x, y), str(val), fontsize=font_size, fontname="Helv")

    try:
        doc.save(output_path)
        return True
    except Exception as e:
        print(f"Error saving PDF {output_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate I-9 Forms (Coordinate Based)")
    parser.add_argument("--data", default=DEFAULT_INPUT_JSON, help="Path to HR JSON data")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE_PDF, help="Path to I-9 PDF template")
    parser.add_argument("--out", default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--font", default=DEFAULT_FONT_PATH, help="Path to signature font file")
    args = parser.parse_args()

    # 1. Load Data
    records = DataLoader.load(args.data)
    if not records:
        print("No records found. Exiting.")
        return

    # 2. Setup Output
    if not os.path.exists(args.out):
        os.makedirs(args.out)

    print(f"--- Generating I-9s for {len(records)} employees ---")
    
    success_count = 0
    for record in records:
        # UPDATED KEY: Uses 'employee_id' instead of 'Employee_ID'
        emp_id = record.get("employee_id", "Unknown")
        filename = f"I9_{emp_id}.pdf"
        output_path = os.path.join(args.out, filename)
        
        if fill_i9_pdf(record, args.template, output_path, args.font):
            print(f"Generated: {filename}")
            success_count += 1
        else:
            print(f"Failed: {filename}")

    print(f"--- Complete. Generated {success_count} I-9s. ---")

if __name__ == "__main__":
    main()


# python main.py --data data/plan_census.json --template plan_census.html --out output/eligibility
