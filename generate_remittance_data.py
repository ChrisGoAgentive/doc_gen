import json
import random
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# --- CONFIGURATION ---
OUTPUT_DIR = 'data'
NUM_PAY_PERIODS = 3
EMPLOYEES_PER_PERIOD = 15
COMPANY_NAME = "ACME CORPORATION"
COMPANY_BANK = "SILICON VALLEY BANK"
PLAN_PROVIDER = "FIDELITY TRUST CO"
PLAN_ACCOUNT = "Acme 401(k) Trust"

def main():
    print(f"--- Generating Remittance Testing Data ---")
    
    payroll_summaries = []
    wire_confirms = []
    remittance_details = []

    # Generate dates for the last few pay periods
    base_date = datetime.now() - timedelta(days=60)

    for i in range(NUM_PAY_PERIODS):
        # 1. TIMING LOGIC
        # Pay Date is usually a Friday
        pay_date_obj = base_date + timedelta(weeks=i*2)
        while pay_date_obj.weekday() != 4:
            pay_date_obj += timedelta(days=1)
            
        pay_date_str = pay_date_obj.strftime('%Y-%m-%d')
        
        # Remittance Date: 1 to 5 business days AFTER Pay Date
        days_to_remit = random.randint(1, 5)
        remit_date_obj = pay_date_obj + timedelta(days=days_to_remit)
        # Skip weekends
        if remit_date_obj.weekday() > 4: 
             remit_date_obj += timedelta(days=2)
        remit_date_str = remit_date_obj.strftime('%Y-%m-%d')
        
        period_start = (pay_date_obj - timedelta(days=13)).strftime('%m/%d/%Y')
        period_end = (pay_date_obj + timedelta(days=0)).strftime('%m/%d/%Y') # Pay date usually matches period end or is offset, using offset for realism in other scripts, but aligning here for simplicity or saying period ends previous Friday
        # Let's align with previous scripts: Pay Period ends previous Friday (day - 7), Pay Date is this Friday
        real_period_end = pay_date_obj - timedelta(days=7)
        real_period_start = real_period_end - timedelta(days=13)
        period_str = f"{real_period_start.strftime('%m/%d/%Y')} - {real_period_end.strftime('%m/%d/%Y')}"

        # 2. GENERATE EMPLOYEE ROSTER & AMOUNTS
        roster = []
        total_gross = 0.0
        total_pre_tax = 0.0
        total_roth = 0.0
        total_match = 0.0
        total_loan = 0.0
        
        for _ in range(EMPLOYEES_PER_PERIOD):
            emp_name = fake.name()
            ssn_last4 = str(fake.random_number(digits=4)).zfill(4)
            
            gross = round(random.uniform(1500.00, 4500.00), 2)
            
            # 80% participate
            if random.random() > 0.2:
                rate = random.choice([0.03, 0.05, 0.10])
                # Randomly split between Pre-tax and Roth
                if random.choice([True, False]):
                    pre_tax = round(gross * rate, 2)
                    roth = 0.0
                else:
                    pre_tax = 0.0
                    roth = round(gross * rate, 2)
                
                # Employer Match (Safe Harbor 4%)
                match = round(gross * 0.04, 2)
                
                # Occasional Loan Repayment
                loan = 50.00 if random.random() > 0.9 else 0.0
            else:
                pre_tax = 0.0
                roth = 0.0
                match = 0.0
                loan = 0.0

            roster.append({
                "name": emp_name,
                "id": f"***-**-{ssn_last4}",
                "gross": gross,
                "pre_tax": pre_tax,
                "roth": roth,
                "loan": loan,
                "match": match,
                "total_deposit": pre_tax + roth + loan + match
            })
            
            total_gross += gross
            total_pre_tax += pre_tax
            total_roth += roth
            total_loan += loan
            total_match += match

        # 3. CALCULATE GRAND TOTALS (The Audit Anchor)
        grand_total_remittance = total_pre_tax + total_roth + total_loan + total_match
        
        # 4. CREATE PAYROLL SUMMARY JOURNAL (Source Document)
        # Typically shows company-wide liabilities
        summary_id = f"PAYSUM-{pay_date_obj.strftime('%Y%m%d')}"
        payroll_summaries.append({
            "document_id": summary_id,
            "company_name": COMPANY_NAME,
            "pay_date": pay_date_str,
            "period": period_str,
            "totals": {
                "gross_pay": f"{total_gross:,.2f}",
                "401k_pre_tax": f"{total_pre_tax:,.2f}",
                "401k_roth": f"{total_roth:,.2f}",
                "401k_loans": f"{total_loan:,.2f}",
                "employer_match": f"{total_match:,.2f}",
                "total_remittance_liability": f"{grand_total_remittance:,.2f}"
            }
        })

        # 5. CREATE WIRE TRANSFER CONFIRMATION (Proof of Cash)
        wire_id = f"WIRE-{fake.random_number(digits=9)}"
        wire_confirms.append({
            "document_id": wire_id,
            "bank_name": COMPANY_BANK,
            "sender": COMPANY_NAME,
            "receiver": PLAN_PROVIDER,
            "account_credit": PLAN_ACCOUNT,
            "transaction_date": remit_date_str, # The critical date for testing timeliness
            "fed_ref": f"FED{fake.random_number(digits=12)}",
            "amount": f"{grand_total_remittance:,.2f}",
            "memo": f"401k Contrib PD {pay_date_str}"
        })

        # 6. CREATE REMITTANCE FILE DETAIL (Breakdown)
        # Lists every employee contribution that makes up the wire
        remit_id = f"REMIT-{pay_date_obj.strftime('%Y%m%d')}"
        remittance_details.append({
            "document_id": remit_id,
            "plan_provider": PLAN_PROVIDER,
            "pay_date": pay_date_str,
            "wire_date": remit_date_str, # Reference the wire
            "wire_id": wire_id,
            "employees": [
                {
                    "name": r['name'],
                    "ssn": r['id'],
                    "pre_tax": f"{r['pre_tax']:.2f}",
                    "roth": f"{r['roth']:.2f}",
                    "loan": f"{r['loan']:.2f}",
                    "match": f"{r['match']:.2f}",
                    "total": f"{r['total_deposit']:.2f}"
                } for r in roster if r['total_deposit'] > 0 # Only list participants
            ],
            "totals": {
                "pre_tax": f"{total_pre_tax:,.2f}",
                "roth": f"{total_roth:,.2f}",
                "loan": f"{total_loan:,.2f}",
                "match": f"{total_match:,.2f}",
                "grand_total": f"{grand_total_remittance:,.2f}"
            }
        })

    # --- SAVE FILES ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(os.path.join(OUTPUT_DIR, 'remittance_payroll_summaries.json'), 'w') as f:
        json.dump(payroll_summaries, f, indent=2)
        print(f"Saved {len(payroll_summaries)} Payroll Summaries")

    with open(os.path.join(OUTPUT_DIR, 'remittance_wire_confirmations.json'), 'w') as f:
        json.dump(wire_confirms, f, indent=2)
        print(f"Saved {len(wire_confirms)} Wire Confirmations")

    with open(os.path.join(OUTPUT_DIR, 'remittance_details.json'), 'w') as f:
        json.dump(remittance_details, f, indent=2)
        print(f"Saved {len(remittance_details)} Remittance Details")

if __name__ == "__main__":
    main()

# python generate_remittance_data.py 
# python main.py --data data/remittance_payroll_summaries.json --template remittance_payroll_summary.html --out output/remittance
# python main.py --data data/remittance_wire_confirmations.json --template remittance_wire_confirmation.html --out output/remittance
# python main.py --data data/remittance_details.json --template remittance_detail.html --out output/remittance