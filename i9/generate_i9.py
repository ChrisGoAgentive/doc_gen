import sys
import os
import argparse
import fitz  # PyMuPDF: pip install pymupdf

# Ensure we can import from utils in the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_utils import DataLoader, DataFormatter
from utils.signature_utils import SignatureGenerator

# Configure the font path for signatures
# Assumes 'fonts' folder is in the project root
DEFAULT_FONT_PATH = os.path.join("fonts", "PlaywriteIN-VariableFont_wght.ttf")

# --- CONFIGURATION ---
DEFAULT_INPUT_JSON = "data/hr_employee_file_rich.json"
DEFAULT_TEMPLATE_PDF = "templates/fi-9_flat.pdf"
DEFAULT_OUTPUT_DIR = "output/i9_forms"

# ==============================================================================
#  STEP 1: COORDINATE FIELD MAPPING
#  This map defines where to place text.
#  Format: [Page Index, X, Y, Font Size, Max Width]
#  
#  *** CRITICAL: PyMuPDF uses a TOP-LEFT origin (0,0 is top-left corner). ***
#  You must measure your X/Y coordinates from the TOP-LEFT of the page.
# ==============================================================================
I9_COORD_MAP = {
    # --- Page 1 ---
    
    # Section 1: Personal Info
    # Adjust these values based on your specific PDF template measurements
    "last_name":        [0, 45, 183, 10, 150], 
    "first_name":       [0, 205, 183, 10, 150], 
    "middle_initial":   [0, 350, 183, 10, 30],
    "other_last_names": [0, 430, 183, 10, 150],
    
    "address":          [0, 45, 210, 10, 300],
    "apt_number":       [0, 238, 210, 10, 50],
    "city":             [0, 310, 210, 10, 100],
    "state":            [0, 470, 210, 10, 40],
    "zip":              [0, 512, 210, 10, 70],
    
    "dob":              [0, 45, 236, 10, 100], # mm/dd/yyyy
    "ssn":              [0, 153, 236, 10, 100, 11.5],
    "email":            [0, 266, 236, 10, 200],
    "phone":            [0, 460, 236, 10, 150],

    # Citizenship Checkboxes
    # For coordinates, point to where the center of the 'X' should go.
    "citizen_check":    [0, 182, 269, 12, 10], 

    "signature_employee": [0, 25, 353, 150, 20, "SIGNATURE"],
    "employee_sig_date": [0, 370, 368, 10, 100],
    
    # --- (Section 2) ---


}

def fill_i9_pdf(record, template_path, output_path, font_path):
    """
    Fills a single I-9 PDF for an employee record using PyMuPDF (fitz) coordinates.
    """
    try:
        # 1. Prepare Data
        identity = record.get("Identity", {})
        
        ssn_raw = identity.get("ssn", "")
        ssn_clean = DataFormatter.format_digits_only(ssn_raw)
        
        dob_raw = identity.get("dob", "")
        dob_formatted = DataFormatter.format_date(dob_raw, output_fmt="%m/%d/%Y")
        
        hire_date = record.get("Hire_Date", "")
        hire_date_fmt = DataFormatter.format_date(hire_date, output_fmt="%m/%d/%Y")
        
        # Use full name as seed for signature
        full_name = f"{identity.get('first_name')} {identity.get('last_name')}"

        # Map Logical Keys -> Actual Values
        data_to_fill = {
            "last_name": identity.get("last_name"),
            "first_name": identity.get("first_name"),
            "middle_initial": "", 
            "address": identity.get("home_address", {}).get("street"),
            "city": identity.get("home_address", {}).get("city"),
            "state": identity.get("home_address", {}).get("state"),
            "zip": identity.get("home_address", {}).get("zip"),
            "ssn": ssn_clean,
            "dob": dob_formatted,
            "employee_sig_date": hire_date_fmt,
            "email": identity.get("work_email"),
            "phone": DataFormatter.format_phone("5551234567"), 
            "citizen_check": "X" if identity.get("citizenship_status", {}).get("code") == 1 else None,
            "first_day_employment": hire_date_fmt,
            
            # Pass the name as the 'value' for the signature fields
            "signature_employee": full_name,
            "signature_employer": "Sarah Connor" # Static HR Rep
        }

        # 2. PyMuPDF Processing
        doc = fitz.open(template_path)
        
        for logical_key, coords in I9_COORD_MAP.items():
            value = data_to_fill.get(logical_key)
            
            if value:
                page_idx = coords[0]
                
                if page_idx < len(doc):
                    page = doc[page_idx]
                    
                    # Check for Signature Flag
                    # Format: [Page, X, Y, Width, Height, "SIGNATURE"]
                    if len(coords) >= 6 and coords[5] == "SIGNATURE":
                        x, y, w, h = coords[1], coords[2], coords[3], coords[4]
                        
                        # Call the updated SignatureGenerator with font path
                        SignatureGenerator.draw_signature(
                            page, x, y, w, h, 
                            seed_text=str(value), 
                            font_path=font_path
                        )
                        
                    # Standard Text
                    else:
                        x, y, font_size = coords[1], coords[2], coords[3]
                        letter_spacing = coords[5] if len(coords) > 5 else 0
                        
                        if letter_spacing > 0:
                            for i, char in enumerate(str(value)):
                                char_x = x + (i * letter_spacing)
                                page.insert_text((char_x, y), char, fontsize=font_size, fontname="helv", color=(0, 0, 0))
                        else:
                            page.insert_text((x, y), str(value), fontsize=font_size, fontname="helv", color=(0, 0, 0))
                else:
                    print(f"Warning: Page index {page_idx} out of range for {logical_key}")

        # 3. Save
        doc.save(output_path)
        return True

    except Exception as e:
        print(f"Failed to generate I-9: {e}")
        import traceback
        traceback.print_exc()
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
    print(f"Using Signature Font: {args.font}")
    
    success_count = 0
    for record in records:
        emp_id = record.get("Employee_ID", "Unknown")
        filename = f"I9_{emp_id}.pdf"
        output_path = os.path.join(args.out, filename)
        
        if fill_i9_pdf(record, args.template, output_path, args.font):
            print(f"Generated: {filename}")
            success_count += 1
    
    print(f"--- Complete. Generated {success_count} I-9 forms. ---")

if __name__ == "__main__":
    main()