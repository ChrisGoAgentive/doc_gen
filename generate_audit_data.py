import json
import random
import os
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker
fake = Faker()

# --- 1. GLOBAL CONFIGURATION VARS ---
OUTPUT_DIR = 'data'
NUM_EMPLOYEES = 10  # How many full sets of documents to generate
COMPANY_NAME = "ACME CORPORATION"
COMPANY_ADDR = "123 Innovation Drive, Tech City, CA 94043"
PLAN_NAME = "ACME CORP 401(K) PROFIT SHARING PLAN"

# Investment Options (Ticker, Name, Share Price)
FUNDS = [
    {"ticker": "VTR2050", "name": "Vanguard Target Retirement 2050", "price": 45.10},
    {"ticker": "VTR2060", "name": "Vanguard Target Retirement 2060", "price": 42.80},
    {"ticker": "SP500",   "name": "S&P 500 Index Fund",              "price": 412.50},
    {"ticker": "INTL",    "name": "International Growth Fund",       "price": 118.20},
    {"ticker": "CO_STK",  "name": "Company Stock Fund",              "price": 15.75},
    {"ticker": "BOND",    "name": "Bond Market Index",               "price": 10.40}
]

def generate_random_allocation_mix():
    """
    Returns a list of funds with percentages that sum EXACTLY to 100.
    """
    # Pick 2 to 4 random funds
    num_funds = random.randint(2, 4)
    selected_funds = random.sample(FUNDS, num_funds)
    
    # Generate random cut points to determine percentages
    cuts = sorted([random.randint(1, 100) for _ in range(num_funds - 1)])
    
    # Calculate intervals
    percentages = []
    current = 0
    for cut in cuts:
        percentages.append(cut - current)
        current = cut
    percentages.append(100 - current) # Ensure last piece sums to 100
    
    # Combine fund info with calculated percentage
    mix = []
    for i, fund in enumerate(selected_funds):
        mix.append({
            "fund_name": fund["name"],
            "share_price": fund["price"],
            "percent_int": percentages[i],       # Integer for math (e.g., 40)
            "percent_str": f"{percentages[i]}%"  # String for display (e.g., "40%")
        })
    return mix

def calculate_taxes(gross_amount):
    """Returns (Fed, FICA, State) based on rough estimates."""
    fed = round(gross_amount * 0.12, 2)
    fica = round(gross_amount * 0.0765, 2)
    state = round(gross_amount * 0.05, 2)
    return fed, fica, state

def main():
    print(f"--- Starting Generation for {NUM_EMPLOYEES} Employees ---")
    
    # Holders for the final JSON lists
    all_allocations = []
    all_paystubs = []
    all_transactions = []

    for _ in range(NUM_EMPLOYEES):
        # =========================================================================
        # STEP 1: DEFINE SHARED VARIABLES ( The "Single Source of Truth" )
        # =========================================================================
        
        # Identity
        emp_id = f"EMP-{fake.random_number(digits=6)}"
        emp_name = fake.name()
        
        # Dates (Audit Trail: Allocation signed -> Pay Period Ends -> Pay Date/Transaction)
        pay_date_obj = fake.date_this_year() # The central date
        pay_date_str = pay_date_obj.strftime('%Y-%m-%d')
        
        # Pay Period is 2 weeks prior
        pay_period_end_obj = datetime.strptime(pay_date_str, '%Y-%m-%d') - timedelta(days=5)
        pay_period_start_obj = pay_period_end_obj - timedelta(days=13)
        pay_period_str = f"{pay_period_start_obj.strftime('%m/%d/%Y')} - {pay_period_end_obj.strftime('%m/%d/%Y')}"
        
        # Allocation Form Date (Signed 30 days before pay date)
        alloc_signed_date_obj = pay_period_start_obj - timedelta(days=random.randint(10, 45))
        alloc_effective_date_obj = pay_period_start_obj # Effective at start of pay period
        
        # Financials
        hourly_rate = round(random.uniform(28.00, 75.00), 2)
        hours_worked = round(random.uniform(78.0, 82.0), 2)
        gross_pay = round(hourly_rate * hours_worked, 2)
        
        # 401k Logic
        contribution_rate = random.choice([0.03, 0.04, 0.05, 0.06, 0.10, 0.15])
        
        # *** KEY AUDIT VARIABLE *** # This exact dollar amount must appear on Pay Stub AND Transaction Summary
        total_401k_deduction = round(gross_pay * contribution_rate, 2)
        
        # *** KEY AUDIT VARIABLE ***
        # This specific mix dictates the Allocation Form AND the Transaction splits
        investment_mix = generate_random_allocation_mix()

        # =========================================================================
        # STEP 2: GENERATE ALLOCATION FORM
        # =========================================================================
        
        # To make it realistic, we'll say their "Current" allocation is just a Target Date fund,
        # and their "New" allocation is the complex mixed generated above.
        
        alloc_doc = {
            "document_id": f"ALLOC-{emp_id}",
            "participant_name": emp_name,
            "participant_id": emp_id,
            "plan_name": PLAN_NAME,
            "request_date": alloc_signed_date_obj.strftime('%Y-%m-%d'),
            "effective_date": alloc_effective_date_obj.strftime('%Y-%m-%d'),
            # Current is simple
            "current_allocation": [
                {"fund": "Vanguard Target Retirement 2050", "percent": "100%"}
            ],
            # New matches our shared 'investment_mix' variable
            "new_allocation": [
                {"fund": i['fund_name'], "percent": i['percent_str']} for i in investment_mix
            ]
        }
        all_allocations.append(alloc_doc)

        # =========================================================================
        # STEP 3: GENERATE PAY STUB
        # =========================================================================
        
        fed_tax, fica_tax, state_tax = calculate_taxes(gross_pay)
        health_ins = 60.00
        
        total_deductions = round(fed_tax + fica_tax + state_tax + health_ins + total_401k_deduction, 2)
        net_pay = round(gross_pay - total_deductions, 2)

        pay_stub_doc = {
            "document_id": f"STUB-{emp_id}-{pay_date_obj.strftime('%Y%m%d')}",
            "company_name": COMPANY_NAME,
            "company_address": COMPANY_ADDR,
            "employee_name": emp_name,
            "employee_id": emp_id,
            "pay_period": pay_period_str,
            "pay_date": pay_date_str, # Matches Transaction Date
            "check_number": str(fake.random_number(digits=5)),
            "earnings": [
                {
                    "desc": "Regular Pay", 
                    "rate": f"{hourly_rate:.2f}", 
                    "hours": f"{hours_worked}", 
                    "amount": f"{gross_pay:,.2f}"
                }
            ],
            "taxes": [
                {"desc": "Federal Withholding", "amount": f"{fed_tax:,.2f}"},
                {"desc": "Social Security & Medicare", "amount": f"{fica_tax:,.2f}"},
                {"desc": "State Withholding", "amount": f"{state_tax:,.2f}"}
            ],
            "deductions": [
                {"desc": "Health Insurance", "amount": f"{health_ins:,.2f}"},
                # *** AUDIT CHECKPOINT: This must match total_401k_deduction ***
                {"desc": "401(k) Deferral", "amount": f"{total_401k_deduction:,.2f}"} 
            ],
            "totals": {
                "gross": f"{gross_pay:,.2f}",
                "deductions": f"{total_deductions:,.2f}",
                "net": f"{net_pay:,.2f}"
            }
        }
        all_paystubs.append(pay_stub_doc)

        # =========================================================================
        # STEP 4: GENERATE TRANSACTION SUMMARY
        # =========================================================================
        
        trx_items = []
        running_split_total = 0.0
        
        # Loop through the SAME 'investment_mix' used in Step 2
        for index, fund in enumerate(investment_mix):
            is_last = (index == len(investment_mix) - 1)
            
            # Calculate how much of the deduction goes to this fund
            if is_last:
                # Math integrity: Last fund takes the remaining pennies
                split_amount = round(total_401k_deduction - running_split_total, 2)
            else:
                split_amount = round(total_401k_deduction * (fund['percent_int'] / 100.0), 2)
            
            running_split_total += split_amount
            
            # Calculate units bought
            units_bought = round(split_amount / fund['share_price'], 3)
            
            if split_amount > 0:
                trx_items.append({
                    "date": pay_date_str, # Matches Pay Stub Date
                    "desc": "Payroll Contribution - Employee",
                    "fund": fund['fund_name'], # Matches Allocation Form Name
                    "amount": f"{split_amount:,.2f}",
                    "price": f"{fund['share_price']:.2f}",
                    "units": f"{units_bought:.3f}"
                })
        
        # Add employer match (simplified 50% match into first fund)
        match_amt = round(total_401k_deduction * 0.5, 2)
        match_fund = investment_mix[0] # Match goes to primary fund
        match_units = round(match_amt / match_fund['share_price'], 3)
        
        trx_items.append({
            "date": pay_date_str,
            "desc": "Payroll Contribution - Employer Match",
            "fund": match_fund['fund_name'],
            "amount": f"{match_amt:,.2f}",
            "price": f"{match_fund['share_price']:.2f}",
            "units": f"{match_units:.3f}"
        })

        trx_doc = {
            "document_id": f"TRX-{emp_id}",
            "plan_name": PLAN_NAME,
            "participant_name": emp_name,
            "account_number": f"ACT-{fake.random_number(digits=8)}",
            "period_start": pay_period_start_obj.strftime('%Y-%m-%d'),
            "period_end": (pay_date_obj + timedelta(days=30)).strftime('%Y-%m-%d'),
            "transactions": trx_items
        }
        all_transactions.append(trx_doc)

    # =========================================================================
    # STEP 5: SAVE FILES
    # =========================================================================
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save Allocation Forms
    with open(os.path.join(OUTPUT_DIR, '401k_allocation_forms.json'), 'w') as f:
        json.dump(all_allocations, f, indent=2)
        print(f"Saved {len(all_allocations)} Allocation Forms")

    # Save Pay Stubs
    with open(os.path.join(OUTPUT_DIR, 'pay_stubs.json'), 'w') as f:
        json.dump(all_paystubs, f, indent=2)
        print(f"Saved {len(all_paystubs)} Pay Stubs")

    # Save Transaction Summaries
    with open(os.path.join(OUTPUT_DIR, '401k_transaction_summaries.json'), 'w') as f:
        json.dump(all_transactions, f, indent=2)
        print(f"Saved {len(all_transactions)} Transaction Summaries")

if __name__ == "__main__":
    main()