import json
import random
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# --- CONFIGURATION ---
OUTPUT_DIR = 'data'
NUM_EMPLOYEES = 5
PLAN_NAME = "ACME CORP 401(K) PROFIT SHARING PLAN"
TRUSTEE_NAME = "FIDELITY INSTITUTIONAL SERVICES"
PERIOD_DESC = "October 1, 2024 - December 31, 2024"
START_DATE = "2024-10-01"
END_DATE = "2024-12-31"

# --- THE GOLDEN THREAD: FUND PERFORMANCE ---
# These rates define the truth. Both the Plan and the Participant
# must reflect these exact return rates for the math to check out.
FUND_PERFORMANCE = [
    {"name": "Vanguard Target Retirement 2050", "ticker": "VFIFX", "rate": 0.0425, "price_open": 44.50, "price_close": 46.39},
    {"name": "Vanguard Target Retirement 2060", "ticker": "VTTSX", "price_open": 41.20, "rate": 0.0410, "price_close": 42.89},
    {"name": "Fidelity 500 Index Fund",         "ticker": "FXAIX", "rate": 0.0615, "price_open": 158.30, "price_close": 168.04},
    {"name": "Metropolitan West Total Return",  "ticker": "MWTRX", "rate": 0.0120, "price_open": 10.15, "price_close": 10.27},
    {"name": "Company Stock Fund",              "ticker": "ACME",  "rate": -0.0250, "price_open": 18.00, "price_close": 17.55} # A loss!
]

def generate_fund_activity(opening_balance, fund_rate):
    """
    Calculates the closing balance based on the strict rate.
    Formula: Closing = Opening + (Opening * Rate)
    We are excluding contributions/fees in this specific test to isolate Earnings.
    """
    earnings = round(opening_balance * fund_rate, 2)
    closing = round(opening_balance + earnings, 2)
    return earnings, closing

def main():
    print(f"--- Generating Investment Earnings Data ---")
    
    participant_stmts = []
    employer_stmts = []

    # =========================================================================
    # 1. GENERATE EMPLOYER FUND STATEMENT (The "Master" Record)
    # =========================================================================
    # This represents the total assets of the plan. It should be large.
    
    plan_assets = []
    total_plan_open = 0.0
    total_plan_close = 0.0
    
    for fund in FUND_PERFORMANCE:
        # The plan holds millions in each fund
        fund_open = round(random.uniform(2_000_000.00, 15_000_000.00), 2)
        earnings, fund_close = generate_fund_activity(fund_open, fund['rate'])
        
        plan_assets.append({
            "fund_name": fund['name'],
            "ticker": fund['ticker'],
            "opening_balance": f"{fund_open:,.2f}",
            "earnings": f"{earnings:,.2f}",
            "closing_balance": f"{fund_close:,.2f}",
            "rate_display": f"{fund['rate']*100:.2f}%" # Displayed for easier checking, or hide to make auditor calculate it
        })
        
        total_plan_open += fund_open
        total_plan_close += fund_close

    employer_stmt = {
        "document_id": "TRUST-STMT-2024-Q4",
        "trustee": TRUSTEE_NAME,
        "plan_name": PLAN_NAME,
        "period": PERIOD_DESC,
        "account_number": f"TRUST-{fake.random_number(digits=9)}",
        "funds": plan_assets,
        "summary": {
            "opening_balance": f"{total_plan_open:,.2f}",
            "total_earnings": f"{total_plan_close - total_plan_open:,.2f}",
            "closing_balance": f"{total_plan_close:,.2f}"
        }
    }
    employer_stmts.append(employer_stmt)

    # =========================================================================
    # 2. GENERATE PARTICIPANT STATEMENTS (The "Sample" Records)
    # =========================================================================
    
    for _ in range(NUM_EMPLOYEES):
        emp_id = f"EMP-{fake.random_number(digits=6)}"
        emp_name = fake.name()
        
        # Determine Participant's Mix (They hold 2-3 of the available funds)
        my_funds = random.sample(FUND_PERFORMANCE, k=random.randint(2, 3))
        
        emp_assets = []
        total_emp_open = 0.0
        total_emp_close = 0.0
        
        for fund in my_funds:
            # Employee holds thousands, not millions
            fund_open = round(random.uniform(5_000.00, 150_000.00), 2)
            
            # *** CRITICAL AUDIT STEP ***
            # We MUST use the exact same rate as the Master Fund
            earnings, fund_close = generate_fund_activity(fund_open, fund['rate'])
            
            emp_assets.append({
                "fund_name": fund['name'],
                "opening_balance": f"{fund_open:,.2f}",
                "earnings": f"{earnings:,.2f}", # This figure is what auditors test
                "closing_balance": f"{fund_close:,.2f}",
                # ROI is usually calculated by the auditor, but we ensure the math works
            })
            
            total_emp_open += fund_open
            total_emp_close += fund_close

        participant_stmt = {
            "document_id": f"STMT-{emp_id}-2024Q4",
            "participant_name": emp_name,
            "participant_id": emp_id,
            "plan_name": PLAN_NAME,
            "period": PERIOD_DESC,
            "funds": emp_assets,
            "summary": {
                "opening_balance": f"{total_emp_open:,.2f}",
                "change_in_value": f"{total_emp_close - total_emp_open:,.2f}",
                "closing_balance": f"{total_emp_close:,.2f}"
            }
        }
        participant_stmts.append(participant_stmt)

    # --- SAVE FILES ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(os.path.join(OUTPUT_DIR, 'employer_fund_statements.json'), 'w') as f:
        json.dump(employer_stmts, f, indent=2)
        print(f"Saved {len(employer_stmts)} Employer Fund Statements")

    with open(os.path.join(OUTPUT_DIR, 'participant_statements.json'), 'w') as f:
        json.dump(participant_stmts, f, indent=2)
        print(f"Saved {len(participant_stmts)} Participant Statements")

if __name__ == "__main__":
    main()

# python generate_investment_earnings_data.py 
# python main.py --data data/employer_fund_statements.json --template employer_fund_statement.html --out output/investment_earnings_testing
# python main.py --data data/participant_statements.json --template participant_account_statement.html --out output/investment_earnings_testing