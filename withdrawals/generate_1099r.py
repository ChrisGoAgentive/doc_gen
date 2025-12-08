import json
import os
import sys
import argparse
import datetime
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, TextStringObject

# --- CONFIGURATION ---
INPUT_JSON = "data/401k_withdrawal.json"
TEMPLATE_PDF = "templates/f1099r.pdf"
DEFAULT_OUTPUT_DIR = "output/1099r_forms"

# PAYER DETAILS (Static for ACME Corp)
PAYER_INFO = {
    "name": "ACME CORP 401(K) TRUST",
    "address": "123 Business Rd",
    "city_state_zip": "Tech City, CA 90210",
    "tin": "99-1234567"
}

# ==============================================================================
#  STEP 1: MAP YOUR FIELDS HERE
#  Open your 'debug_basic_1099r.pdf'. Look at the text written inside the boxes.
#  Copy that exact text and paste it as the value for the corresponding key below.
# ==============================================================================
PDF_FIELD_MAP = {
    # --- Payer & Recipient Info ---
    # The large block on the top left for Payer Name/Address
    "payer_block": "f2_01[0]", 
    
    # Payer's Federal ID / TIN
    "payer_tin": "f2_02[0]",
    
    # Recipient's SSN
    "recipient_ssn": "f2_03[0]",
    
    # Recipient's Name
    "recipient_name": "f2_04[0]",
    
    # Recipient's Street Address
    "recipient_address": "f2_05[0]",
    
    # Recipient's City, State, ZIP
    "recipient_city_state_zip": "f2_06[0]",
    
    # Account Number (Bottom Left)
    "account_id": "f2_07[0]",

    # --- Financial Boxes (Right Column) ---
    # Box 1: Gross distribution
    "gross_amt": "f2_08[0]",
    
    # Box 2a: Taxable amount
    "taxable_amt": "f2_09[0]",
    
    # Box 4: Federal income tax withheld
    "fed_tax": "f2_11[0]",
    
    # Box 5: Employee contributions (Designated Roth, etc.)
    "emp_contrib": "f2_12[0]",
    
    # Box 7: Distribution code (e.g., '1', '7', '4')
    "dist_code": "f2_14[0]",
    
    # Box 7: IRA/SEP/SIMPLE Checkbox
    "ira_checkbox": "c2_4[0]",
    
    # Box 14: State tax withheld
    "state_tax": "f2_23[0]",
    
    # Box 15: State code
    "state_code": "f2_25[0]",
    
    # Box 16: State distribution
    "state_dist": "f2_27[0]"
}

def calculate_age(dob_str, tax_year):
    """Calculates age by the end of the tax year."""
    try:
        dob = datetime.datetime.strptime(dob_str, "%Y-%m-%d")
        return tax_year - dob.year
    except Exception:
        return 30 

def determine_distribution_code(age, reason="Separation"):
    """
    Logic to determine Box 7 code.
    Code 1: Early distribution (under 59 1/2).
    Code 7: Normal distribution (over 59 1/2).
    Code 4: Death.
    """
    if reason == "Death":
        return "4"
    if age >= 59.5:
        return "7"
    return "1" 

def generate_1099r(output_dir):
    # 1. Setup
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    if not os.path.exists(INPUT_JSON):
        print(f"Error: Input file {INPUT_JSON} not found.")
        return

    with open(INPUT_JSON, 'r') as f:
        withdrawals = json.load(f)

    print(f"--- Generating 1099-R Forms for {len(withdrawals)} records ---")
    print(f"Template: {os.path.abspath(TEMPLATE_PDF)}")
    print(f"Output:   {os.path.abspath(output_dir)}")

    success_count = 0
    
    # 2. Process each record
    for record in withdrawals:
        data = record['data']
        doc_id = record['document_id']
        
        # --- PREPARE DATA FROM JSON ---
        gross_str = data.get('gross_withdrawal_amount', '0.00').replace(',', '')
        gross_float = float(gross_str)
        taxable_float = gross_float 
        fed_tax = taxable_float * 0.20
        state_tax = taxable_float * 0.05
        
        tax_year = 2025
        age = calculate_age(data.get('dob', '1980-01-01'), tax_year)
        dist_code = determine_distribution_code(age)

        # Map Logical Keys -> Actual Values
        form_data = {
            "payer_block": f"{PAYER_INFO['name']}\n{PAYER_INFO['address']}\n{PAYER_INFO['city_state_zip']}",
            "payer_tin": PAYER_INFO['tin'],
            "recipient_ssn": data.get('ssn'),
            "recipient_name": data.get('participant_name'),
            "recipient_address": data.get('address'),
            "recipient_city_state_zip": f"{data.get('city')}, {data.get('state')} {data.get('zip')}",
            "account_id": data.get('account_id'),
            "gross_amt": f"{gross_float:.2f}",
            "taxable_amt": f"{taxable_float:.2f}",
            "fed_tax": f"{fed_tax:.2f}",
            "emp_contrib": "0.00",
            "dist_code": dist_code,
            "ira_checkbox": False, # False = Unchecked
            "state_tax": f"{state_tax:.2f}",
            "state_code": f"{data.get('state')}",
            "state_dist": f"{gross_float:.2f}"
        }
        
        # Build the specific map for THIS PDF: { "topmostSubform...f2_08": "123.45" }
        current_pdf_map = {}
        for logical_key, pdf_field_name in PDF_FIELD_MAP.items():
            if logical_key in form_data:
                current_pdf_map[pdf_field_name] = form_data[logical_key]

        # --- FILL PDF ---
        try:
            reader = PdfReader(TEMPLATE_PDF)
            writer = PdfWriter()
            writer.append_pages_from_reader(reader)

            # AcroForm Copy
            if "/AcroForm" in reader.root_object:
                writer.root_object[NameObject("/AcroForm")] = reader.root_object["/AcroForm"]

            # AcroForm Cleanup (XFA Removal + NeedAppearances)
            if "/AcroForm" in writer.root_object:
                acroform = writer.root_object["/AcroForm"]
                if "/XFA" in acroform:
                    del acroform["/XFA"]
                acroform[NameObject("/NeedAppearances")] = BooleanObject(True)

            # Direct Annotation Modification (Robust Write)
            if len(writer.pages) > 0:
                page = writer.pages[0]
                if "/Annots" in page:
                    for annot in page["/Annots"]:
                        annot_obj = annot.get_object()
                        
                        if "/Subtype" in annot_obj and annot_obj["/Subtype"] == "/Widget":
                            field_name = annot_obj.get("/T")
                            
                            # Check if we have data for this field name
                            if field_name and field_name in current_pdf_map:
                                value_to_write = current_pdf_map[field_name]
                                
                                # Handle Checkboxes
                                if annot_obj.get("/FT") == "/Btn":
                                    if value_to_write: # If True/Yes
                                        annot_obj[NameObject("/V")] = NameObject("/Yes")
                                        annot_obj[NameObject("/AS")] = NameObject("/Yes")
                                    else:
                                        annot_obj[NameObject("/V")] = NameObject("/Off")
                                        annot_obj[NameObject("/AS")] = NameObject("/Off")
                                # Handle Text
                                else:
                                    annot_obj[NameObject("/V")] = TextStringObject(str(value_to_write))

            output_filename = f"1099R_{doc_id}.pdf"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, "wb") as output_stream:
                writer.write(output_stream)
            
            success_count += 1
            print(f"Generated: {output_filename}")

        except Exception as e:
            print(f"Failed to generate {doc_id}: {e}")
            import traceback
            traceback.print_exc()
            
    print(f"Successfully generated {success_count} 1099-R forms.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 1099-R Forms")
    parser.add_argument("--out", default=DEFAULT_OUTPUT_DIR, help="Output directory for generated PDFs")
    args = parser.parse_args()
    
    generate_1099r(args.out)
