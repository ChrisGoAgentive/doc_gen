import json
import random
import os
import sys
from datetime import datetime, timedelta
from faker import Faker

# Fix path to find modules in root if running from 'data' or similar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



fake = Faker()


# --- CONFIGURATION ---
OUTPUT_DIR = 'data'
HR_FILE_NAME = 'hr_employee_file_rich.json'
CENSUS_FILE_NAME = 'plan_census.json'

NUM_NEW_EMPLOYEES = 20  # Only used if generating fresh data
COMPANY_NAME = "ACME CORPORATION"
COMPANY_ADDR = "123 Innovation Drive, Tech City, CA 94043"
PLAN_YEAR_END = "2024-12-31"

# Plan Rules
MIN_AGE = 21
MIN_SERVICE_YEARS = 1
ENTRY_FREQUENCY = "Semi-Annual" # Entry dates are 1/1 and 7/1

def calculate_entry_date(hire_date_obj, dob_obj):
    """
    Calculates the exact date an employee enters the plan.
    Rule: Later of (Hire + 1 Year) OR (DOB + 21 Years), then next 1/1 or 7/1.
    """
    # 1. Date they satisfy Service Req
    service_req_date = hire_date_obj.replace(year=hire_date_obj.year + MIN_SERVICE_YEARS)
    
    # 2. Date they satisfy Age Req
    age_req_date = dob_obj.replace(year=dob_obj.year + MIN_AGE)
    
    # 3. Eligibility Date is the LATER of the two
    eligibility_date = max(service_req_date, age_req_date)
    
    # 4. Entry Date is the next Semi-Annual Entry Date (1/1 or 7/1)
    year = eligibility_date.year
    entry_jan = datetime(year, 1, 1).date()
    entry_jul = datetime(year, 7, 1).date()
    entry_next_jan = datetime(year + 1, 1, 1).date()
    
    # Convert eligibility_date (which is a date object) to date for comparison if needed
    # (Here hire_date_obj and dob_obj are expected to be date objects, so eligibility_date is date)
    elig_check = eligibility_date
    
    if elig_check <= entry_jan:
        return entry_jan
    elif elig_check <= entry_jul:
        return entry_jul
    else:
        return entry_next_jan

def load_or_generate_hr_data(filepath):
    """
    Tries to load existing HR data. If missing OR INVALID, generates fresh data.
    Returns: List of employee dictionaries.
    """
    if os.path.exists(filepath):
        print(f"[INFO] Found existing HR file at {filepath}. Checking compatibility...")
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            if isinstance(data, list) and len(data) > 0:
                # Validate critical keys exist in the first record based on hr_employee_file_rich.json
                first_rec = data[0]
                required_keys = ['dob', 'hire_date', 'compensation', 'full_name', 'employee_id']
                
                missing = [k for k in required_keys if k not in first_rec]
                
                if not missing:
                    print(f"[INFO] HR file is valid. Using {len(data)} records.")
                    return data
                else:
                    print(f"[WARN] Existing HR file is missing keys: {missing}. Regenerating fresh data.")
            else:
                 print(f"[WARN] Existing HR file was empty or not a list. Regenerating.")
                 
        except Exception as e:
            print(f"[WARN] Failed to read existing HR file: {e}")
            print("[INFO] Generating fresh data instead.")
    else:
        print(f"[INFO] No HR file found at {filepath}. Generating fresh Master Data.")

    # --- GENERATION LOGIC (Fallback) ---
    # This logic now strictly mimics the schema of the uploaded hr_employee_file_rich.json
    plan_end_date = datetime.strptime(PLAN_YEAR_END, "%Y-%m-%d").date()
    generated_rows = []

    for _ in range(NUM_NEW_EMPLOYEES):
        emp_name = fake.name()
        first_name = emp_name.split(' ')[0]
        last_name = ' '.join(emp_name.split(' ')[1:])
        emp_id = f"EMP-{fake.random_number(digits=6)}"
        
        # Status (Mix of Active and Terminated)
        is_terminated = random.random() < 0.15
        
        # Dates
        dob_obj = fake.date_of_birth(minimum_age=18, maximum_age=60)
        days_employed = random.randint(30, 1800)
        hire_date_obj = plan_end_date - timedelta(days=days_employed)
        
        term_date_str = None
        if is_terminated:
            days_ago = random.randint(1, 360)
            term_date_obj = plan_end_date - timedelta(days=days_ago)
            if term_date_obj > hire_date_obj:
                term_date_str = term_date_obj.strftime('%Y-%m-%d')
            else:
                is_terminated = False 

        # Compensation
        hourly_rate = round(random.uniform(15.00, 85.00), 2)
        
        hr_row = {
            "employee_id": emp_id,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": emp_name,
            "ssn": fake.ssn(), # Format: 000-00-0000
            "dob": dob_obj.strftime('%Y-%m-%d'),
            "address": fake.address().replace('\n', ', '),
            "email": f"{first_name.lower()}.{last_name.lower()}@acmecorp.com",
            "phone": fake.phone_number(),
            "hire_date": hire_date_obj.strftime('%Y-%m-%d'),
            "termination_date": term_date_str,
            "job_title": fake.job(),
            "department": random.choice(["Engineering", "Sales", "HR", "Finance", "Operations"]),
            "manager": fake.name(),
            "status": "Terminated" if is_terminated else "Active",
            "compensation": {
                "type": "Hourly",
                "rate": hourly_rate,
                "currency": "USD"
            },
            "company_name": COMPANY_NAME,
            "company_address": COMPANY_ADDR
        }
        generated_rows.append(hr_row)
    
    # Save the new Master File
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(generated_rows, f, indent=2)
    print(f"[INFO] Created and saved new HR Master File to {filepath}")
    
    return generated_rows

def main():
    print(f"--- Processing Plan Census ---")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    hr_file_path = os.path.join(OUTPUT_DIR, HR_FILE_NAME)
    
    # 1. GET MASTER DATA (Read or Generate)
    hr_employees = load_or_generate_hr_data(hr_file_path)
    
    census_rows = []
    plan_end_date = datetime.strptime(PLAN_YEAR_END, "%Y-%m-%d").date()

    # 2. TRANSFORM INTO CENSUS DATA
    for emp in hr_employees:
        # Parse Dates from HR File strings
        dob_obj = datetime.strptime(emp['dob'], '%Y-%m-%d').date()
        hire_date_obj = datetime.strptime(emp['hire_date'], '%Y-%m-%d').date()
        
        term_date_str = emp['termination_date']
        is_terminated = term_date_str is not None
        
        # Calculate Plan Entry
        entry_date = calculate_entry_date(hire_date_obj, dob_obj)
        
        # Determine Eligibility Status
        if entry_date <= plan_end_date:
            status_code = "ELIGIBLE"
            status_display = "Terminated" if is_terminated else "Active - Eligible"
        else:
            status_code = "NOT_ELIGIBLE"
            status_display = "Active - Not Met"
            entry_date = None # Should not show entry date if not yet entered
        
        # Calculate Enrollment Logic
        enrollment_decision = "N/A"
        enrollment_date = "N/A"
        first_contrib_date = "N/A"
        
        if entry_date:
            # 80% Participate, 20% Waive
            participating = random.random() > 0.2
            
            # Decision Date: 15-45 days prior to Entry Date
            days_prior = random.randint(15, 45)
            # Ensure enrollment doesn't pre-date hire
            decision_dt = entry_date - timedelta(days=days_prior)
            if decision_dt < hire_date_obj:
                 decision_dt = hire_date_obj
            enrollment_date = decision_dt.strftime('%Y-%m-%d')
            
            if participating:
                enrollment_decision = "Participating"
                # First Contribution: Typically 1st payroll after entry date
                # Let's say 7-14 days after entry date
                contrib_dt = entry_date + timedelta(days=random.randint(7, 14))
                first_contrib_date = contrib_dt.strftime('%Y-%m-%d')
            else:
                enrollment_decision = "Waived"
                first_contrib_date = "N/A"
            
        # Calculate/Estimate Financials based on HR Data
        # (HR file has rate, we calculate approximate annual gross)
        hourly_rate = emp['compensation']['rate']
        
        # Generate hours for the plan year
        if is_terminated:
             # Logic: rough portion of year worked
             if term_date_str:
                 term_date = datetime.strptime(term_date_str, '%Y-%m-%d').date()
                 days_worked_in_year = (term_date - datetime(plan_end_date.year, 1, 1).date()).days
                 days_worked_in_year = max(0, min(365, days_worked_in_year)) # Clamp
                 hours = int((days_worked_in_year / 365) * 2080)
             else:
                 hours = 0
        else:
             hours = random.randint(1800, 2200) # Full time variance

        gross_comp = round(hours * hourly_rate, 2)
        
        # Mask SSN for Census Report
        ssn_raw = emp['ssn']
        ssn_masked = f"***-**-{ssn_raw.split('-')[-1]}" if '-' in ssn_raw else f"***-**-{ssn_raw[-4:]}"

        census_row = {
            "name": emp['full_name'],
            "id": emp['employee_id'],
            "ssn": ssn_masked,
            "dob": emp['dob'],
            "hire_date": emp['hire_date'],
            "term_date": term_date_str if term_date_str else "",
            "hours": f"{hours:,.0f}",
            "compensation": f"{gross_comp:,.2f}",
            "status": status_display,
            "eligibility_code": status_code,
            "entry_date": entry_date.strftime('%Y-%m-%d') if entry_date else "N/A",
            "enrollment_decision": enrollment_decision,
            "enrollment_date": enrollment_date,
            "first_contribution_date": first_contrib_date
        }
        census_rows.append(census_row)

    # Wrap Census in document container
    census_doc = [{
        "document_id": f"CENSUS-{PLAN_YEAR_END.replace('-','')}",
        "company_name": COMPANY_NAME,
        "plan_year_end": PLAN_YEAR_END,
        "employees": census_rows,
        "summary": {
            "total_employees": len(census_rows),
            "total_eligible": len([e for e in census_rows if e['eligibility_code'] == "ELIGIBLE"])
        }
    }]

    # --- SAVE CENSUS FILE ---
    census_path = os.path.join(OUTPUT_DIR, CENSUS_FILE_NAME)
    with open(census_path, 'w') as f:
        json.dump(census_doc, f, indent=2)
        print(f"[SUCCESS] Saved Plan Census to {census_path}")
        print(f"          (Based on {len(census_rows)} employees from Master HR File)")

if __name__ == "__main__":
    main()