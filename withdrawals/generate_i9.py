import json
import os
import argparse
import datetime
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, TextStringObject

# --- CONFIGURATION ---
INPUT_JSON = "data/401k_withdrawal.json"
TEMPLATE_PDF = "templates/fi-9.pdf" # Using the clean template
DEFAULT_OUTPUT_DIR = "output/401k_withdrawals/i9_forms"

# --- FIELD MAPPING ---
# Based on the text visible in your debug_map_fi-9.pdf
PDF_FIELD_MAP = {
    "last_name": "Last Name (Family Name)",
    "first_name": "First Name Given Name",
    "middle_initial": "Employee Middle Initial (if any)",
    "other_names": "Employee Other Last Names Used (if any)",
    "address": "Address Street Number and Name",
    "apt": "Apt Number (if any)",
    "city": "City or Town",
    "state": "State",
    "zip": "ZIP Code",
    "dob": "Date of Birth mmddyyyy",
    "ssn": "US Social Security Number",
    "email": "Employees E-mail Address",
    "phone": "Telephone Number",
    "date_signed": "Today's Date mmddyyy"
}

def split_name(full_name):
    """Splits 'First Last' into ('First', 'Last', 'M')"""
    parts = full_name.split()
    if len(parts) == 1:
        return parts[0], "", ""
    elif len(parts) == 2:
        return parts[0], parts[1], ""
    else:
        # Simplistic handling for Middle Initial
        return parts[0], parts[-1], parts[1][0]

def generate_i9(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    if not os.path.exists(INPUT_JSON):
        print(f"Error: Input file {INPUT_JSON} not found.")
        return

    with open(INPUT_JSON, 'r') as f:
        employees = json.load(f)

    print(f"--- Generating I-9 Forms for {len(employees)} records ---")
    print(f"Template: {TEMPLATE_PDF}")
    print(f"Output:   {output_dir}")

    success_count = 0
    
    for record in employees:
        data = record['data']
        doc_id = record['document_id']
        
        # 1. Prepare Data
        first, last, mi = split_name(data.get('participant_name', ''))
        
        # Map Logical Keys -> PDF Field Names -> Values
        # We construct a dictionary of { "PDF Field Name": "Value" }
        field_data_map = {}
        
        field_data_map[PDF_FIELD_MAP["last_name"]] = last
        field_data_map[PDF_FIELD_MAP["first_name"]] = first
        field_data_map[PDF_FIELD_MAP["middle_initial"]] = mi
        field_data_map[PDF_FIELD_MAP["other_names"]] = "N/A"
        
        field_data_map[PDF_FIELD_MAP["address"]] = data.get('address', '')
        field_data_map[PDF_FIELD_MAP["apt"]] = "" # JSON doesn't have Apt, leave blank
        field_data_map[PDF_FIELD_MAP["city"]] = data.get('city', '')
        field_data_map[PDF_FIELD_MAP["state"]] = data.get('state', '')
        field_data_map[PDF_FIELD_MAP["zip"]] = data.get('zip', '')
        
        # Date Formatting: YYYY-MM-DD -> MM/DD/YYYY
        try:
            dob_dt = datetime.datetime.strptime(data.get('dob', ''), "%Y-%m-%d")
            field_data_map[PDF_FIELD_MAP["dob"]] = dob_dt.strftime("%m/%d/%Y")
        except:
            field_data_map[PDF_FIELD_MAP["dob"]] = data.get('dob', '')

        field_data_map[PDF_FIELD_MAP["ssn"]] = data.get('ssn', '')
        field_data_map[PDF_FIELD_MAP["email"]] = data.get('email', '')
        field_data_map[PDF_FIELD_MAP["phone"]] = data.get('phone', '')
        
        # Use auth_date as signature date
        try:
            auth_dt = datetime.datetime.strptime(data.get('auth_date', ''), "%Y-%m-%d")
            field_data_map[PDF_FIELD_MAP["date_signed"]] = auth_dt.strftime("%m/%d/%Y")
        except:
             field_data_map[PDF_FIELD_MAP["date_signed"]] = ""

        # Citizenship Status
        is_citizen = data.get('is_us_citizen', False)

        # --- FILL PDF (Direct Annotation Mod) ---
        try:
            reader = PdfReader(TEMPLATE_PDF)
            writer = PdfWriter()
            writer.append_pages_from_reader(reader)

            # AcroForm Copy & Cleanup (XFA Removal)
            if "/AcroForm" in reader.root_object:
                writer.root_object[NameObject("/AcroForm")] = reader.root_object["/AcroForm"]
            
            if "/AcroForm" in writer.root_object:
                acroform = writer.root_object["/AcroForm"]
                if "/XFA" in acroform:
                    del acroform["/XFA"]
                acroform[NameObject("/NeedAppearances")] = BooleanObject(True)

            # Iterate Fields
            if len(writer.pages) > 0:
                page = writer.pages[0]
                if "/Annots" in page:
                    for annot in page["/Annots"]:
                        annot_obj = annot.get_object()
                        
                        if "/Subtype" in annot_obj and annot_obj["/Subtype"] == "/Widget":
                            field_name = annot_obj.get("/T")
                            
                            # 1. Handle Text Fields
                            if field_name and field_name in field_data_map:
                                value = field_data_map[field_name]
                                annot_obj[NameObject("/V")] = TextStringObject(str(value))
                            
                            # 2. Handle Citizenship Checkbox
                            # The I-9 usually has checkboxes named specifically. 
                            # We look for the "Citizen" checkbox if is_citizen is True
                            if is_citizen and field_name:
                                # Logic: If the field name contains "Citizen" and "1", check it.
                                # This is a heuristic because we don't have the exact checkbox name from the debug text.
                                # Common I-9 names: "Qr1", "Citizen of the United States", "Check Box1"
                                if "Citizen" in str(field_name) and "1" in str(field_name):
                                     if annot_obj.get("/FT") == "/Btn":
                                        annot_obj[NameObject("/V")] = NameObject("/Yes")
                                        annot_obj[NameObject("/AS")] = NameObject("/Yes")

            output_filename = f"I9_{doc_id}.pdf"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, "wb") as output_stream:
                writer.write(output_stream)
            
            success_count += 1
            print(f"Generated: {output_filename}")

        except Exception as e:
            print(f"Failed to generate {doc_id}: {e}")
            import traceback
            traceback.print_exc()

    print(f"Successfully generated {success_count} I-9 forms.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate I-9 Forms")
    parser.add_argument("--out", default=DEFAULT_OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()
    
    generate_i9(args.out)