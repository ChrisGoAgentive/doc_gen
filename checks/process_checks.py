import json
import random
import os
import sys
from datetime import datetime, timedelta

# Fix path to allow importing from parent utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_utils import DataLoader

# --- Configuration ---
DEFAULT_OUTPUT_FILE = "data/checks.json"

# Static Payer Information
PAYER_INFO = {
    "payer_name": "ACME CORPORATION",
    "payer_address": "123 Innovation Drive",
    "payer_city_state_zip": "Tech City, CA 94043",
    "bank_name": "SILICON VALLEY CREDIT UNION",
    "bank_location": "Palo Alto, CA",
    "bank_routing": "122000218",
    "account_number": "9988776655"
}

def generate_random_date(start_year=2024):
    start = datetime(start_year, 1, 1)
    end = datetime(start_year, 12, 31)
    return (start + timedelta(days=random.randint(0, (end - start).days))).strftime("%Y-%m-%d")

def generate_synthetic_checks(count=10):
    checks = []
    vendors = ["Staples", "PG&E", "WeWork", "Salesforce", "AWS", "FedEx", "Uline", "Cisco", "Dell", "Apple"]
    memos = ["Invoice #1023", "Monthly Service", "Consulting Fee", "Supplies", "Reimbursement", "Equipment"]
    
    current_check_num = 5000
    
    for _ in range(count):
        current_check_num += 1
        checks.append({
            "check_number": str(current_check_num),
            "date": generate_random_date(),
            "payee_name": random.choice(vendors),
            "amount": round(random.uniform(50.00, 5000.00), 2),
            "memo": random.choice(memos),
            "signature_text": "John Doe", # For the HTML template fallback
            **PAYER_INFO
        })
    return checks

def checks_from_expenses(expenses_path):
    if not os.path.exists(expenses_path):
        print(f"Warning: {expenses_path} not found.")
        return []
    
    # Use DataLoader for robustness
    expenses = DataLoader.load(expenses_path)
    checks = []
    current_check_num = 10000
    
    for exp in expenses:
        if exp.get("Approval_Status") == "Approved":
            current_check_num += 1
            raw_date = exp.get("Transaction_Date", "")
            date_str = raw_date.split("T")[0] if "T" in raw_date else raw_date
            
            checks.append({
                "check_number": str(current_check_num),
                "date": date_str,
                "payee_name": exp.get("Vendor_Name", "Unknown Vendor"),
                "amount": exp.get("Total_Amount", 0.0),
                "memo": f"Inv: {exp.get('Journal_Entry_ID', '')[:8]}",
                "signature_text": "Jane Smith",
                **PAYER_INFO
            })
    return checks

def checks_from_payroll(payroll_path):
    if not os.path.exists(payroll_path):
        print(f"Warning: {payroll_path} not found.")
        return []
        
    registers = DataLoader.load(payroll_path)
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
                "memo": f"Payroll {register.get('pay_period')}",
                "signature_text": "CEO Name",
                **PAYER_INFO
            })
    return checks

def main():
    print("--- Processing Check Data ---")
    
    all_checks = []
    
    # 1. Random
    all_checks.extend(generate_synthetic_checks(10))
    
    # 2. Expenses
    all_checks.extend(checks_from_expenses("data/expenses.json"))
    
    # 3. Payroll
    all_checks.extend(checks_from_payroll("data/payroll_registers.json"))
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DEFAULT_OUTPUT_FILE), exist_ok=True)
    
    with open(DEFAULT_OUTPUT_FILE, 'w') as f:
        json.dump(all_checks, f, indent=4)

    print(f"Generated {len(all_checks)} check records in {DEFAULT_OUTPUT_FILE}")

if __name__ == "__main__":
    main()