import json
import random
import argparse
import os
from datetime import datetime, timedelta

# --- Configuration ---
DEFAULT_OUTPUT_FILE = "data/checks.json"

# Static Payer Information (The User's Company)
PAYER_INFO = {
    "payer_name": "ACME CORPORATION",
    "payer_address": "123 Innovation Drive",
    "payer_city_state_zip": "Tech City, CA 94043",
    "bank_name": "SILICON VALLEY CREDIT UNION",
    "bank_location": "Palo Alto, CA",
    "bank_routing": "122000218",
    "account_number": "9988776655"
}

# --- Helpers ---

def generate_random_date(start_year=2024):
    start = datetime(start_year, 1, 1)
    end = datetime(start_year, 12, 31)
    return (start + timedelta(days=random.randint(0, (end - start).days))).strftime("%Y-%m-%d")

def generate_random_check_number(start=1000):
    return str(random.randint(start, start + 5000))

def generate_synthetic_checks(count=10):
    """Generates completely random check data."""
    checks = []
    vendors = ["Staples", "PG&E", "WeWork", "Salesforce", "AWS", "FedEx", "Uline", "Cisco"]
    memos = ["Invoice #1023", "Monthly Service", "Consulting Fee", "Supplies", "Reimbursement"]
    
    current_check_num = 5000
    
    for _ in range(count):
        current_check_num += 1
        checks.append({
            "check_number": str(current_check_num),
            "date": generate_random_date(),
            "payee_name": random.choice(vendors),
            "amount": round(random.uniform(50.00, 5000.00), 2),
            "memo": random.choice(memos),
            **PAYER_INFO # Merge payer/bank info
        })
    return checks

def checks_from_expenses(expenses_path):
    """Converts approved expenses into vendor checks."""
    if not os.path.exists(expenses_path):
        print(f"Warning: {expenses_path} not found. Skipping expenses.")
        return []
        
    with open(expenses_path, 'r') as f:
        expenses = json.load(f)
        
    checks = []
    current_check_num = 10000
    
    for exp in expenses:
        # Only pay approved expenses
        if exp.get("Approval_Status") == "Approved":
            current_check_num += 1
            
            # Parse date to ensure format
            raw_date = exp.get("Transaction_Date", "")
            date_str = raw_date.split("T")[0] if "T" in raw_date else raw_date
            
            checks.append({
                "check_number": str(current_check_num),
                "date": date_str,
                "payee_name": exp.get("Vendor_Name", "Unknown Vendor"),
                "amount": exp.get("Total_Amount", 0.0),
                "memo": f"Inv: {exp.get('Journal_Entry_ID', '')[:8]} - {exp.get('GL_Account_Name', '')}",
                **PAYER_INFO
            })
    print(f"Generated {len(checks)} checks from expenses.")
    return checks

def checks_from_payroll(payroll_path):
    """Converts payroll entries into employee paychecks."""
    if not os.path.exists(payroll_path):
        print(f"Warning: {payroll_path} not found. Skipping payroll.")
        return []
        
    with open(payroll_path, 'r') as f:
        registers = json.load(f)
        
    checks = []
    current_check_num = 20000
    
    for register in registers:
        pay_date = register.get("pay_date", "")
        
        for entry in register.get("entries", []):
            current_check_num += 1
            checks.append({
                "check_number": str(current_check_num),
                "date": pay_date,
                "payee_name": entry.get("Employee_Name"),
                "amount": entry.get("Net_Pay", 0.0),
                "memo": f"Payroll {register.get('pay_period')} - Dept: {entry.get('Department')}",
                **PAYER_INFO
            })
            
    print(f"Generated {len(checks)} checks from payroll.")
    return checks

# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Generate Check JSON Data")
    parser.add_argument("--mode", choices=["random", "expenses", "payroll", "all"], default="all", help="Source of data")
    parser.add_argument("--count", type=int, default=10, help="Number of checks (random mode only)")
    parser.add_argument("--out", default=DEFAULT_OUTPUT_FILE, help="Output JSON file path")
    args = parser.parse_args()

    all_checks = []

    # 1. Random Data
    if args.mode in ["random", "all"]:
        all_checks.extend(generate_synthetic_checks(args.count))

    # 2. Expense Data
    if args.mode in ["expenses", "all"]:
        all_checks.extend(checks_from_expenses("data/expenses.json"))

    # 3. Payroll Data
    if args.mode in ["payroll", "all"]:
        all_checks.extend(checks_from_payroll("data/payroll_registers.json"))

    # Save
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w') as f:
        json.dump(all_checks, f, indent=4)

    print(f"--- Successfully generated {len(all_checks)} checks in {args.out} ---")

if __name__ == "__main__":
    main()