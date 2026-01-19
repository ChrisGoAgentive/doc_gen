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

# Output Filenames
FILE_HR = 'hr_personnel_files.json'
FILE_TIME = 'time_cards.json'
FILE_PAYROLL = 'payroll_register_extracts.json'

def generate_daily_hours(total_target):
    """
    Distributes total hours across 10 working days (2 weeks).
    Returns a list of daily hours.
    """
    days = 10
    base = total_target / days
    daily = []
    current_sum = 0
    
    for _ in range(days - 1):
        # Add slight variance but keep it realistic (e.g., 7.5 to 8.5)
        h = round(random.uniform(base - 0.5, base + 0.5), 2)
        daily.append(h)
        current_sum += h
    
    # Adjust last day to match target exactly
    last_day = round(total_target - current_sum, 2)
    daily.append(last_day)
    return daily

def main():
    print(f"--- Generating Pay Rate Test Data for {NUM_EMPLOYEES} Employees ---")
    
    hr_files = []
    time_cards = []
    payroll_registers = []

    for _ in range(NUM_EMPLOYEES):
        # 1. SHARED IDENTITY & DATES
        emp_id = f"EMP-{fake.random_number(digits=6)}"
        emp_name = fake.name()
        dob = fake.date_of_birth(minimum_age=18, maximum_age=65).strftime('%Y-%m-%d')
        
        # Hire Date (1-5 years ago)
        hire_date_obj = fake.date_this_decade(before_today=True, after_today=False)
        hire_date = hire_date_obj.strftime('%Y-%m-%d')

        # Pay Period (Recent)
        period_end_obj = datetime.now() - timedelta(days=random.randint(0, 30))
        # Snap to Friday
        while period_end_obj.weekday() != 4:
            period_end_obj -= timedelta(days=1)
            
        period_start_obj = period_end_obj - timedelta(days=13) # 2 week period
        pay_date_obj = period_end_obj + timedelta(days=7) # Paid 1 week later
        
        period_str = f"{period_start_obj.strftime('%m/%d/%Y')} - {period_end_obj.strftime('%m/%d/%Y')}"

        # 2. RATE VARIABLES (Source: HR File)
        hourly_rate = round(random.uniform(22.00, 65.00), 2)
        
        # Rate Effective Date (Must be BEFORE period start)
        rate_effective_obj = period_start_obj - timedelta(days=random.randint(20, 300))
        rate_effective_date = rate_effective_obj.strftime('%Y-%m-%d')

        # 3. TIME VARIABLES (Source: Time Card)
        total_hours = round(random.uniform(75.0, 85.0), 2)
        daily_hours_list = generate_daily_hours(total_hours)
        
        # 4. CALCULATION (Source: Payroll Register)
        gross_pay = round(hourly_rate * total_hours, 2)

        # --- GENERATE HR PERSONNEL FILE ---
        hr_doc = {
            "document_id": f"HR-{emp_id}",
            "company_name": COMPANY_NAME,
            "employee_name": emp_name,
            "employee_id": emp_id,
            "dob": dob,
            "hire_date": hire_date,
            "department": fake.job(),
            "status": "Active",
            "compensation": {
                "type": "Hourly",
                "rate": f"{hourly_rate:.2f}",
                "effective_date": rate_effective_date,
                "approved_by": fake.name()
            }
        }
        hr_files.append(hr_doc)

        # --- GENERATE TIME CARD ---
        # Map hours to specific dates
        time_entries = []
        current_day = period_start_obj
        day_idx = 0
        
        # Simple logic: Mon-Fri work week
        while current_day <= period_end_obj:
            if current_day.weekday() < 5: # Mon-Fri
                h = daily_hours_list[day_idx] if day_idx < len(daily_hours_list) else 0
                time_entries.append({
                    "date": current_day.strftime('%m/%d/%Y'),
                    "day": current_day.strftime('%A'),
                    "hours": h
                })
                day_idx += 1
            else:
                 time_entries.append({
                    "date": current_day.strftime('%m/%d/%Y'),
                    "day": current_day.strftime('%A'),
                    "hours": "OFF"
                })
            current_day += timedelta(days=1)

        time_doc = {
            "document_id": f"TC-{emp_id}-{period_end_obj.strftime('%Y%m%d')}",
            "company_name": COMPANY_NAME,
            "employee_name": emp_name,
            "employee_id": emp_id,
            "period": period_str,
            "department": hr_doc['department'],
            "entries": time_entries,
            "total_hours": f"{total_hours:.2f}",
            "supervisor_sign": fake.name()
        }
        time_cards.append(time_doc)

        # --- GENERATE PAYROLL REGISTER EXTRACT ---
        pay_doc = {
            "document_id": f"REG-{emp_id}-{pay_date_obj.strftime('%Y%m%d')}",
            "company_name": COMPANY_NAME,
            "run_date": pay_date_obj.strftime('%m/%d/%Y'),
            "period": period_str,
            "employee_name": emp_name,
            "employee_id": emp_id,
            "line_items": [
                {
                    "type": "Regular Earnings",
                    "rate": f"{hourly_rate:.2f}",   # Matches HR
                    "hours": f"{total_hours:.2f}",  # Matches Time Card
                    "amount": f"{gross_pay:,.2f}"   # Math Check
                }
            ],
            "total_gross": f"{gross_pay:,.2f}"
        }
        payroll_registers.append(pay_doc)

    # --- SAVE FILES ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(os.path.join(OUTPUT_DIR, FILE_HR), 'w') as f:
        json.dump(hr_files, f, indent=2)
        print(f"Saved {len(hr_files)} Personnel Files to {FILE_HR}")

    with open(os.path.join(OUTPUT_DIR, FILE_TIME), 'w') as f:
        json.dump(time_cards, f, indent=2)
        print(f"Saved {len(time_cards)} Time Cards to {FILE_TIME}")

    with open(os.path.join(OUTPUT_DIR, FILE_PAYROLL), 'w') as f:
        json.dump(payroll_registers, f, indent=2)
        print(f"Saved {len(payroll_registers)} Payroll Registers to {FILE_PAYROLL}")

if __name__ == "__main__":
    main()

# python main.py --data data/hr_personnel_files.json --template personnel_file.html --out output/payrate
# python main.py --data data/time_cards.json --template time_card.html --out output/payrate
# python main.py --data data/payroll_register_extracts.json --template payroll_register_extract.html --out output/payrate