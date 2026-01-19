import json
import random
import os
import sys
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# --- CONFIGURATION ---
INPUT_FILE = 'data/hr_employee_file_rich.json'
OUTPUT_FILE = 'data/i9_compliance_data.json'

# --- CONSTANTS ---
CITIZENSHIP_STATUSES = ["1", "2", "3", "4"] # 1: Citizen, 2: Non-citizen national, 3: Perm Resident, 4: Alien authorized

LIST_A_DOCS = [
    {"title": "U.S. Passport", "issuing": "U.S. Department of State"},
    {"title": "Permanent Resident Card", "issuing": "USCIS"},
]
LIST_B_DOCS = [
    {"title": "Driver's License", "issuing": "DMV"},
    {"title": "ID Card", "issuing": "State Government"},
]
LIST_C_DOCS = [
    {"title": "Social Security Card", "issuing": "SSA"},
    {"title": "Birth Certificate", "issuing": "State Vital Records"},
]

def generate_document_data(doc_type_list):
    """Generates random document details."""
    doc = random.choice(doc_type_list)
    return {
        "title": doc['title'],
        "issuing": doc['issuing'],
        "number": fake.bothify(text='??######'),
        "exp": fake.future_date(end_date="+10y").strftime('%m/%d/%Y')
    }

def main():
    print(f"--- Generating I-9 Compliance Data ---")
    
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file {INPUT_FILE} not found. Please run generate_census_data.py first.")
        return

    with open(INPUT_FILE, 'r') as f:
        employees = json.load(f)

    i9_records = []

    for emp in employees:
        # 1. Base Data from HR File
        # We copy the existing rich data so we don't lose anything
        record = emp.copy()

        # 2. Section 1 Extras
        record["middle_initial"] = "N/A" # Simplified
        record["other_last_names"] = "N/A"
        record["apt_number"] = "" # Address usually has it or not, simplified
        
        # Citizenship (Weighted towards Citizens for standard testing)
        if random.random() > 0.1:
            record["citizenship_stat"] = "1"
            record["citizen_check"] = "X"
        else:
            record["citizenship_stat"] = "3" # Permanent Resident
            record["citizen_check"] = "" 
            # Logic for other checkboxes would go here if coordinates mapped

        # 3. Section 2: Document Logic
        # Strategy: 80% use List A (Passport), 20% use List B + C
        use_list_a = random.random() > 0.2
        
        if use_list_a:
            doc = generate_document_data(LIST_A_DOCS)
            record["list_a_doc_title_user"] = doc['title']
            record["list_a_issuing_auth_user"] = doc['issuing']
            record["list_a_doc_number_user"] = doc['number']
            record["list_a_doc_exp_user"] = doc['exp']
            
            # Clear B and C
            record["list_b_doc_title_user"] = ""
            record["list_b_issuing_auth_user"] = ""
            record["list_b_doc_number_user"] = ""
            record["list_b_doc_exp_user"] = ""
            record["list_c_doc_title_user"] = ""
            record["list_c_issuing_auth_user"] = ""
            record["list_c_doc_number_user"] = ""
            record["list_c_doc_exp_user"] = ""
        else:
            # List B
            doc_b = generate_document_data(LIST_B_DOCS)
            record["list_b_doc_title_user"] = doc_b['title']
            record["list_b_issuing_auth_user"] = doc_b['issuing']
            record["list_b_doc_number_user"] = doc_b['number']
            record["list_b_doc_exp_user"] = doc_b['exp']
            
            # List C
            doc_c = generate_document_data(LIST_C_DOCS)
            record["list_c_doc_title_user"] = doc_c['title']
            record["list_c_issuing_auth_user"] = doc_c['issuing']
            record["list_c_doc_number_user"] = doc_c['number']
            record["list_c_doc_exp_user"] = "N/A" # SS cards don't expire usually
            
            # Clear A
            record["list_a_doc_title_user"] = ""
            record["list_a_issuing_auth_user"] = ""
            record["list_a_doc_number_user"] = ""
            record["list_a_doc_exp_user"] = ""

        # 4. Employer Certification
        # Hire Date is already in record['hire_date'] (YYYY-MM-DD)
        # We need MM/DD/YYYY for the form
        try:
            hd_obj = datetime.strptime(record['hire_date'], '%Y-%m-%d')
            first_day = hd_obj.strftime('%m/%d/%Y')
            
            # Signed within 3 days of hire
            sign_date_obj = hd_obj + timedelta(days=random.randint(0, 3))
            sign_date = sign_date_obj.strftime('%m/%d/%Y')
        except:
            first_day = record['hire_date']
            sign_date = record['hire_date']

        record["first_day_employment_user"] = first_day
        record["employer_sig_date_user"] = sign_date
        
        # Employer Rep Info
        record["employer_name_user"] = "Jane Doe" 
        record["signature_employer_user"] = "Jane Doe"
        record["rep_title"] = "HR Manager"
        record["rep_last_name"] = "Doe"
        record["rep_first_name"] = "Jane"
        
        # Business Info
        record["business_name_user"] = record.get("company_name", "ACME Corp")
        full_addr = record.get("company_address", "123 Innovation Dr, Tech City, CA 94043")
        record["business_address_user"] = full_addr.split(',')[0]
        record["rep_city"] = "Tech City"
        record["rep_state"] = "CA"
        record["rep_zip"] = "94043"

        i9_records.append(record)

    # --- SAVE ---
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(i9_records, f, indent=2)
    
    print(f"Success! Generated {len(i9_records)} I-9 compliance records.")
    print(f"Output saved to: {OUTPUT_FILE}")
    print("You can now run generate_i9.py using this file.")

if __name__ == "__main__":
    main()