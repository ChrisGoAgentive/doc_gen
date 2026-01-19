import json
import os
import sys
import random
from datetime import datetime

# Fix path to find modules in root if running from 'data' or similar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- CONFIGURATION ---
INPUT_FILE = 'data/plan_census.json'
OUTPUT_FILE = 'data/enrollment_forms.json'
PLAN_NAME = "ACME CORP 401(K) PROFIT SHARING PLAN"

def main():
    print(f"--- Generating Enrollment Decision Forms ---")
    
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file {INPUT_FILE} not found. Please run generate_census_data.py first.")
        return

    try:
        with open(INPUT_FILE, 'r') as f:
            census_data = json.load(f)
            # Census is a list wrapped in a doc, typically [ { "employees": [...] } ]
            # or just the dict depending on how previous script saved it.
            # Based on previous output, it's a list containing one document object.
            if isinstance(census_data, list):
                employees = census_data[0].get('employees', [])
            else:
                employees = census_data.get('employees', [])
    except Exception as e:
        print(f"Error reading census file: {e}")
        return

    enrollment_forms = []

    for emp in employees:
        decision = emp.get('enrollment_decision')
        
        # We only generate forms for those who are eligible and have made a decision
        if decision not in ["Participating", "Waived"]:
            continue

        # Generate some form-specific details consistent with the decision
        if decision == "Participating":
            contrib_rate = random.randint(3, 10) # 3% to 10%
            contrib_type = "Pre-Tax"
            beneficiary_name = "Generic Beneficiary (Spouse/Trust)"
            beneficiary_rel = "Spouse"
        else:
            contrib_rate = 0
            contrib_type = "N/A"
            beneficiary_name = "N/A"
            beneficiary_rel = "N/A"

        form_doc = {
            "document_id": f"ENROLL-{emp['id']}",
            "plan_name": PLAN_NAME,
            "participant_name": emp['name'],
            "participant_id": emp['id'],
            "ssn_masked": emp['ssn'], # Already masked in census
            "dob": emp['dob'],
            "hire_date": emp['hire_date'],
            "entry_date": emp['entry_date'],
            
            # Decision Data
            "decision": decision, # 'Participating' or 'Waived'
            "sign_date": emp['enrollment_date'],
            
            # Participation Details
            "contribution_rate": contrib_rate,
            "contribution_type": contrib_type,
            
            # Beneficiary (Synthetic for the form)
            "beneficiary": {
                "name": beneficiary_name,
                "relationship": beneficiary_rel,
                "share": "100%"
            }
        }
        enrollment_forms.append(form_doc)

    # --- SAVE ---
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(enrollment_forms, f, indent=2)
    
    print(f"Success! Generated {len(enrollment_forms)} Enrollment Forms.")
    print(f"Output saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

# python main.py --data data/enrollment_forms.json --template enrollment_form.html --out output/eligibility
