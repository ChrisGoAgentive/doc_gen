import json
import os
import random
import hashlib
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker
fake = Faker()

def get_deterministic_seed(input_string):
    """Generates a consistent seed based on the input string (e.g., Employee ID)."""
    return int(hashlib.sha256(input_string.encode('utf-8')).hexdigest(), 16) % (10 ** 8)

def generate_401k_data(employee, sep_date_str):
    """
    Transforms a single HR employee record into a rich 401(k) data object
    suitable for both Statements and Withdrawal forms.
    """
    emp_id = employee.get("Employee_ID")
    
    identity = employee.get("Identity", {})
    compensation = employee.get("Compensation", {})
    benefits = employee.get("Benefits_Elections", {})

    # Helper function for currency formatting (American Standard: 1,234.56)
    def fmt(val):
        return "{:,.2f}".format(val)

    # 1. Basic Participant Info
    full_name = identity.get("full_name")
    address_obj = identity.get("home_address", {})
    
    dob_raw = identity.get("dob", "1980-01-01")
    # Separation date passed in from main loop for consistency
    
    # 2. Financial Simulation
    salary = compensation.get("Annual_Salary", 50000)
    contribution_pct = benefits.get("401k_Pct", 5)
    
    # Simulate balances
    prior_year_bal = round(salary * random.uniform(0.5, 2.0), 2)
    ytd_contrib_emp = round(salary * (contribution_pct / 100) * 0.75, 2)
    ytd_contrib_er = round(ytd_contrib_emp * 0.5, 2) # 50% match
    gains = round((prior_year_bal + ytd_contrib_emp) * random.uniform(0.03, 0.08), 2)
    
    # Total Current Balance (Used for gross calculations)
    current_bal = round(prior_year_bal + ytd_contrib_emp + ytd_contrib_er + gains, 2)

    # 3. Investment Funds breakdown
    funds = [
        {"name": "Vanguard Target Retirement 2050", "share": 0.6},
        {"name": "S&P 500 Index Fund", "share": 0.3},
        {"name": "International Growth Fund", "share": 0.1}
    ]
    
    # We calculate using floats first to ensure math is correct before formatting
    investments_raw = []
    running_total = 0.0
    
    # Calculate funds (handling rounding to ensure sum matches total)
    for i, fund in enumerate(funds):
        if i == len(funds) - 1:
            # Last item takes the remainder to ensure exact match
            share_bal = round(current_bal - running_total, 2)
        else:
            share_bal = round(current_bal * fund["share"], 2)
            running_total += share_bal
            
        # Logic Change: Withdrawal column must equal the total balance to zero it out
        beg = round(share_bal * 0.9, 2)
        dep = round(share_bal * 0.05, 2)
        gain = round(share_bal * 0.05, 2)
        # Adjust gain slightly to ensure precise match to share_bal
        gain = round(share_bal - beg - dep, 2)
        
        # Gross Withdrawal = The entire balance
        gross_withdrawal = share_bal 
        
        investments_raw.append({
            "name": fund["name"],
            "beg_bal": beg,
            "deposits": dep,
            "gains": gain,
            "transfers": 0.00,
            "withdrawals": -abs(gross_withdrawal), # Negative to show money leaving
            "end_bal": 0.00, # Zero Balance
            "units": 0.000   # Zero Units
        })

    # Calculate Investment Totals (Float)
    inv_total_raw = {
        "beg_bal": sum(i["beg_bal"] for i in investments_raw),
        "deposits": sum(i["deposits"] for i in investments_raw),
        "gains": sum(i["gains"] for i in investments_raw),
        "transfers": 0.00,
        "withdrawals": sum(i["withdrawals"] for i in investments_raw),
        "end_bal": 0.00,
        "units": 0.000
    }
    
    # Convert Investment data to Formatted Strings for Output
    investments_formatted = []
    for i in investments_raw:
        investments_formatted.append({
            "name": i["name"],
            "beg_bal": fmt(i["beg_bal"]),
            "deposits": fmt(i["deposits"]),
            "gains": fmt(i["gains"]),
            "transfers": fmt(i["transfers"]),
            "withdrawals": fmt(i["withdrawals"]),
            "end_bal": fmt(i["end_bal"]),
            "units": "{:,.3f}".format(i["units"])
        })

    # 4. Sources Breakdown (100% Vesting & Zero Out Logic)
    # Split total into Employee (66%) and Employer (34%)
    emp_share_amt = round(current_bal * 0.66, 2)
    er_share_amt = round(current_bal - emp_share_amt, 2) # Remainder
    
    # Sources Raw Data
    sources_raw = [
        {
            "name": "Employee Deferral",
            "beg_bal": round(prior_year_bal * 0.66, 2),
            "deposits": ytd_contrib_emp,
            "gains": round(gains * 0.66, 2),
            "withdrawals": -abs(emp_share_amt), # Full withdrawal
            "end_bal": 0.00,
            "pct_vested": "100%",
            "vested_bal": 0.00
        },
        {
            "name": "Employer Match",
            "beg_bal": round(prior_year_bal * 0.34, 2),
            "deposits": ytd_contrib_er,
            "gains": round(gains * 0.34, 2),
            "withdrawals": -abs(er_share_amt), # Full withdrawal
            "end_bal": 0.00,
            "pct_vested": "100%",
            "vested_bal": 0.00
        }
    ]

    # Convert Sources to Formatted Strings
    sources_formatted = []
    for s in sources_raw:
        sources_formatted.append({
            "name": s["name"],
            "beg_bal": fmt(s["beg_bal"]),
            "deposits": fmt(s["deposits"]),
            "gains": fmt(s["gains"]),
            "withdrawals": fmt(s["withdrawals"]),
            "end_bal": fmt(s["end_bal"]),
            "pct_vested": s["pct_vested"],
            "vested_bal": fmt(s["vested_bal"])
        })

    # 5. Withdrawal & Fee Logic
    withdrawal_fee = 50.00
    
    # 100% Payout Calculation
    # Net Payout is the total balance minus the fee.
    net_payout = round(current_bal - withdrawal_fee, 2)

    # Activity Ledger
    # Logic Update: Only show the $50 fee. No other math or totals in the list.
    
    activity_entries = [
        {"desc": "Withdrawal Fee", "date": sep_date_str, "amount": f"-{fmt(withdrawal_fee)}"}
    ]
    
    # Since the list only has the fee, the total displayed should effectively be the fee.
    activity_net_change = -abs(withdrawal_fee)
    
    # Calculate an auth date derived from separation date
    auth_date_obj = datetime.strptime(sep_date_str, "%Y-%m-%d") - timedelta(days=2)
    auth_date_str = auth_date_obj.strftime("%Y-%m-%d")

    doc_data = {
        "document_id": f"401K-{emp_id}",
        "data": {
            # --- Withdrawal Form Fields ---
            "plan_name": "ACME CORP 401(K) PROFIT SHARING PLAN",
            "participant_name": full_name,
            "participant_id": emp_id,
            "address": address_obj.get("street"),
            "city": address_obj.get("city"),
            "state": address_obj.get("state"),
            "zip": address_obj.get("zip"),
            "ssn": identity.get("ssn"),
            "dob": dob_raw,
            "phone": fake.phone_number(), # Use global faker
            "email": identity.get("work_email"),
            "location_code": f"LOC-{random.randint(100,999)}",
            "is_us_citizen": identity.get("citizenship_status", {}).get("code") == 1,
            
            # Withdrawal Specifics
            "confirmation_num": str(random.randint(10000000, 99999999)),
            "auth_date": auth_date_str,
            "sep_date": sep_date_str,
            "withdrawal_fee": fmt(withdrawal_fee),
            "est_net_payout": fmt(net_payout),
            "gross_withdrawal_amount": fmt(current_bal),
            
            # --- Statement Fields ---
            "account_id": f"ACT-{random.randint(10000,99999)}",
            "contribution_rate": f"{contribution_pct}%",
            
            # Investment Table
            "investments": investments_formatted,
            "inv_total": {
                "beg_bal": fmt(inv_total_raw["beg_bal"]),
                "deposits": fmt(inv_total_raw["deposits"]),
                "gains": fmt(inv_total_raw["gains"]),
                "transfers": fmt(inv_total_raw["transfers"]),
                "withdrawals": fmt(inv_total_raw["withdrawals"]),
                "end_bal": fmt(inv_total_raw["end_bal"]),
                "units": "{:,.3f}".format(inv_total_raw["units"])
            },
            
            # Sources Table (Enforcing 100% Vesting)
            "sources": sources_formatted,
            "src_total": {
                "beg_bal": fmt(prior_year_bal),
                "deposits": fmt(ytd_contrib_emp + ytd_contrib_er),
                "gains": fmt(gains),
                "withdrawals": fmt(-abs(current_bal)),
                "end_bal": fmt(0.00),
                "vested_bal": fmt(0.00)
            },
            
            # History Table
            "history": {
                "ytd_withdrawals": {"employee": fmt(0.00), "employer": fmt(0.00), "total": fmt(0.00)},
                "prev_year_bal": {
                    "employee": fmt(round(prior_year_bal * 0.66, 2)),
                    "employer": fmt(round(prior_year_bal * 0.34, 2)),
                    "total": fmt(prior_year_bal)
                }
            },
            
            # Activity Table (Showing ONLY the fee)
            "activity": activity_entries,
            "activity_total": fmt(activity_net_change)
        }
    }
    return doc_data

def generate_letter_data(employee, reason, sep_date_str):
    """
    Generates data for specific separation letters based on the reason.
    """
    emp_id = employee.get("Employee_ID")
    identity = employee.get("Identity", {})
    full_name = identity.get("full_name")
    address_obj = identity.get("home_address", {})
    
    # Common Data
    common_data = {
        "employee_name": full_name,
        "emp_address": address_obj.get("street"),
        "emp_city_state_zip": f"{address_obj.get('city')}, {address_obj.get('state')} {address_obj.get('zip')}",
        "date": datetime.now().strftime("%B %d, %Y"),
        "company_name": "ACME Corp",
        "company_address": "123 Business Rd, Tech City, CA 90210",
        "sep_date": sep_date_str,
        "hr_rep": "Sarah Connor"
    }

    if reason == "resignation":
        # Data for resignation_template.html
        return {
            "document_id": f"RESIGN-{emp_id}",
            "data": common_data # Template uses data.field
        }
    
    elif reason == "separation":
        # Data for separation_template.html
        # Needs specific state
        common_data["state"] = address_obj.get("state") # Governing law state
        return {
            "document_id": f"SEP-{emp_id}",
            "data": common_data
        }
        
    elif reason == "death":
        # Data for death_notification_template.html
        return {
            "document_id": f"DEATH-{emp_id}",
            "data": common_data
        }
    
    return None

def process_withdrawals_file(input_file='data/hr_employee_file_rich.json'):
    if not os.path.exists(input_file):
        print(f"Error: Source file '{input_file}' not found.")
        return

    print(f"--- Processing HR File: {input_file} ---")
    
    with open(input_file, 'r') as f:
        employees = json.load(f)
        
    print(f"Found {len(employees)} employees.")
    
    all_401k_docs = []
    
    # Letter lists
    resignations = []
    separations = []
    death_notifications = []
    
    for emp in employees:
        emp_id = emp.get("Employee_ID")
        
        # Consistent Seed for this employee loop
        seed = get_deterministic_seed(emp_id)
        random.seed(seed)
        Faker.seed(seed)
        fake.seed_instance(seed)

        # 1. Simulate Separation Date (Common for all docs for this employee)
        sep_date_obj = datetime.now() - timedelta(days=random.randint(5, 30))
        sep_date_str = sep_date_obj.strftime("%Y-%m-%d")

        # 2. Generate 401k Data (Assuming withdrawal happens upon separation)
        doc_data = generate_401k_data(emp, sep_date_str)
        all_401k_docs.append(doc_data)

        # 3. Simulate Status Change Logic
        # "if the status of the employee is separated"
        # Since source data is all "Active", we randomly assign separation status for demonstration.
        # Let's say 40% of the active file is actually processing a separation event.
        is_separating = random.choice([True, False, True, False, False]) # ~40% chance
        
        # Override: The user implies we should process if status IS separated. 
        # To make the script functional on the provided data, we effectively 
        # pretend this flag exists.
        current_status = emp.get("Status")
        
        if is_separating or current_status != "Active":
            # Assign Random Reason
            reason = random.choice(["resignation", "separation", "death"])
            
            letter_doc = generate_letter_data(emp, reason, sep_date_str)
            
            if letter_doc:
                if reason == "resignation":
                    resignations.append(letter_doc)
                elif reason == "separation":
                    separations.append(letter_doc)
                elif reason == "death":
                    death_notifications.append(letter_doc)
        
    if not os.path.exists('data'):
        os.makedirs('data')
        
    # Save 401k Data
    with open('data/401k_withdrawal.json', 'w') as f:
        json.dump(all_401k_docs, f, indent=2)
    print(f"Generated data/401k_withdrawal.json ({len(all_401k_docs)} records)")
    
    # Save Letter Data
    if resignations:
        with open('data/resignations.json', 'w') as f:
            json.dump(resignations, f, indent=2)
        print(f"Generated data/resignations.json ({len(resignations)} records)")
        
    if separations:
        with open('data/separations.json', 'w') as f:
            json.dump(separations, f, indent=2)
        print(f"Generated data/separations.json ({len(separations)} records)")
        
    if death_notifications:
        with open('data/death_notifications.json', 'w') as f:
            json.dump(death_notifications, f, indent=2)
        print(f"Generated data/death_notifications.json ({len(death_notifications)} records)")

    print("Data processing complete. 100% Withdrawal logic + Separation Letter logic applied.")

if __name__ == "__main__":
    process_withdrawals_file()