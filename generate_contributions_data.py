import json
import random
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# --- CONFIGURATION ---
OUTPUT_DIR = 'data'
NUM_EMPLOYEES = 5
COMPANY_NAME = "ACME CORPORATION"
PLAN_NAME = "ACME CORP 401(K) PROFIT SHARING PLAN"

def main():
    print(f"--- Generating Contribution Testing Data ---")
    
    election_forms = []
    payroll_registers = []

    # loop to create diverse scenarios
    for i in range(NUM_EMPLOYEES):
        # 1. Identity
        emp_id = f"EMP-{fake.random_number(digits=6)}"
        emp_name = fake.name()
        
        # 2. Define Scenario (Deterministic for variety)
        # Scenarios:
        # 0: Pre-Tax Percentage
        # 1: Roth Percentage
        # 2: Pre-Tax Dollar Amount
        # 3: Roth Dollar Amount
        # 4: Both (Split) Percentage
        
        if i == 0:
            scenario = "Pre-Tax Only (%)"
            method = "Percent"
            pre_tax_val = random.randint(3, 15)
            roth_val = 0
        elif i == 1:
            scenario = "Roth Only (%)"
            method = "Percent"
            pre_tax_val = 0
            roth_val = random.randint(3, 10)
        elif i == 2:
            scenario = "Pre-Tax Only ($)"
            method = "Dollar"
            pre_tax_val = random.randrange(50, 400, 25)
            roth_val = 0
        elif i == 3:
            scenario = "Roth Only ($)"
            method = "Dollar"
            pre_tax_val = 0
            roth_val = random.randrange(25, 200, 25)
        else:
            scenario = "Split (Pre-Tax & Roth)"
            method = "Percent"
            pre_tax_val = 6
            roth_val = 4

        # 3. Dates
        pay_date_obj = fake.date_this_year()
        # Election signed 45 days before pay date
        election_date = (pay_date_obj - timedelta(days=45)).strftime('%Y-%m-%d')
        
        pay_date_str = pay_date_obj.strftime('%Y-%m-%d')
        period_end = pay_date_obj - timedelta(days=5)
        period_start = period_end - timedelta(days=13)
        period_str = f"{period_start.strftime('%m/%d/%Y')} - {period_end.strftime('%m/%d/%Y')}"

        # 4. Create ELECTION FORM Data
        election_doc = {
            "document_id": f"ELECTION-{emp_id}",
            "participant_name": emp_name,
            "participant_id": emp_id,
            "plan_name": PLAN_NAME,
            "sign_date": election_date,
            "effective_date": period_start.strftime('%Y-%m-%d'),
            "data": {
                "method": method,         # 'Percent' or 'Dollar'
                "pre_tax_value": pre_tax_val,
                "roth_value": roth_val
            }
        }
        election_forms.append(election_doc)

        # 5. Create PAYROLL REGISTER Data (The Calculation)
        hourly_rate = round(random.uniform(28.00, 65.00), 2)
        hours = 80.0
        gross_pay = round(hourly_rate * hours, 2)
        
        # Calculate Deductions based on Election
        deduct_pre_tax = 0.0
        deduct_roth = 0.0
        
        if method == "Percent":
            if pre_tax_val > 0:
                deduct_pre_tax = round(gross_pay * (pre_tax_val / 100.0), 2)
            if roth_val > 0:
                deduct_roth = round(gross_pay * (roth_val / 100.0), 2)
        else: # Dollar
            if pre_tax_val > 0:
                deduct_pre_tax = float(pre_tax_val)
            if roth_val > 0:
                deduct_roth = float(roth_val)

        # Simple Tax Logic (Pre-tax lowers base)
        taxable_gross = gross_pay - deduct_pre_tax
        fed_tax = round(taxable_gross * 0.12, 2)
        fica = round(gross_pay * 0.0765, 2)
        state_tax = round(taxable_gross * 0.05, 2)
        
        net_pay = round(gross_pay - deduct_pre_tax - deduct_roth - fed_tax - fica - state_tax, 2)

        payroll_doc = {
            "document_id": f"PAYREG-{emp_id}-{pay_date_obj.strftime('%Y%m%d')}",
            "company_name": COMPANY_NAME,
            "run_date": pay_date_str,
            "period": period_str,
            "employee_name": emp_name,
            "employee_id": emp_id,
            "scenario": scenario, # Helper for you to see what logic was used
            "earnings": {
                "rate": f"{hourly_rate:.2f}",
                "hours": f"{hours}",
                "gross": f"{gross_pay:,.2f}"
            },
            "deductions": {
                "pre_tax_401k": f"{deduct_pre_tax:,.2f}",
                "roth_401k": f"{deduct_roth:,.2f}",
                "fed_tax": f"{fed_tax:,.2f}",
                "fica": f"{fica:,.2f}",
                "state": f"{state_tax:,.2f}"
            },
            "net_pay": f"{net_pay:,.2f}"
        }
        payroll_registers.append(payroll_doc)

    # --- SAVE FILES ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(os.path.join(OUTPUT_DIR, 'contribution_elections.json'), 'w') as f:
        json.dump(election_forms, f, indent=2)
        print(f"Saved {len(election_forms)} Election Forms")

    with open(os.path.join(OUTPUT_DIR, 'contribution_payroll_registers.json'), 'w') as f:
        json.dump(payroll_registers, f, indent=2)
        print(f"Saved {len(payroll_registers)} Payroll Registers")

if __name__ == "__main__":
    main()

# python generate_contributions_data.py 
# python main.py --data data/contribution_elections.json --template contribution_election_form.html --out output/contribution_elections
# python main.py --data data/contribution_payroll_registers.json --template contribution_payroll.html --out output/contribution_elections