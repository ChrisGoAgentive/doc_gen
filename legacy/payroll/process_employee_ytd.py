import json
import os
from datetime import datetime
from collections import defaultdict

def safe_round(value):
    """Helper to convert to float and round to 2 decimal places."""
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.00

def process_employee_ytd(input_file='data/payroll_journal.json', output_file='data/employee_ytd_reports.json', target_year=None):
    """
    Groups payroll data by Employee_ID to generate a chronological earnings record
    with running Year-To-Date (YTD) totals for a specific fiscal year.
    Includes an accrued projection for the remainder of the year based on daily rate.
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        journal_entries = json.load(f)

    # Determine Target Year: Default to current year if not provided
    if target_year is None:
        target_year = datetime.now().year
    
    print(f"Processing YTD data for Fiscal Year {target_year}...")

    # Filter entries by the target fiscal year based on Pay_Date
    filtered_entries = []
    for entry in journal_entries:
        pay_date_str = entry.get('Pay_Date', '')
        try:
            # Handle potential ISO format with time
            if 'T' in pay_date_str:
                date_obj = datetime.strptime(pay_date_str.split('T')[0], "%Y-%m-%d")
            else:
                date_obj = datetime.strptime(pay_date_str, "%Y-%m-%d")
            
            if date_obj.year == int(target_year):
                filtered_entries.append(entry)
        except (ValueError, TypeError):
            continue 

    print(f"Found {len(filtered_entries)} transactions for {target_year}.")

    # Group filtered entries by Employee ID
    grouped_data = defaultdict(list)
    for entry in filtered_entries:
        grouped_data[entry['Employee_ID']].append(entry)

    employee_reports = []

    # Process each Employee
    for emp_id, transactions in grouped_data.items():
        # Sort transactions by Pay Date
        transactions.sort(key=lambda x: x.get('Pay_Date', ''))

        first_record = transactions[0]
        emp_name = first_record.get('Employee_Name', 'Unknown')
        department = first_record.get('Department', 'Unknown')

        # Initialize YTD Accumulators
        ytd_accumulators = {
            "Gross_Pay": 0.0,
            "Tax_Fed": 0.0,
            "Tax_State": 0.0,
            "Tax_FICA": 0.0,
            "Benefit_Deduction": 0.0,
            "Net_Pay": 0.0,
            "Hours_Reg": 0.0,
            "Hours_OT": 0.0
        }

        processed_rows = []

        # 1. Calculate Running Totals for Actual Pay Periods
        for trans in transactions:
            row = trans.copy()
            row['is_accrual'] = False
            
            for key in ytd_accumulators:
                val = safe_round(trans.get(key, 0))
                ytd_accumulators[key] = safe_round(ytd_accumulators[key] + val)
                
                row[f"YTD_{key}"] = ytd_accumulators[key]
                row[key] = val 

            processed_rows.append(row)

        # 2. Calculate Accruals (Daily Rate Method)
        if transactions:
            last_record = transactions[-1]
            last_pay_date_str = last_record.get('Pay_Date', '')
            
            # Parse last date
            if 'T' in last_pay_date_str:
                last_date = datetime.strptime(last_pay_date_str.split('T')[0], "%Y-%m-%d")
            else:
                last_date = datetime.strptime(last_pay_date_str, "%Y-%m-%d")
            
            # Determine End of Fiscal Year
            eoy_date = datetime(target_year, 12, 31)
            
            # Calculate remaining unpaid days in the year
            days_remaining = (eoy_date - last_date).days
            
            if days_remaining > 0:
                accrual_row = {
                    "Pay_Period": "ACCRUED (Est.)",
                    "Pay_Date": f"{target_year}-12-31",
                    "Employee_Name": emp_name,
                    "Employee_ID": emp_id,
                    "Department": department,
                    "is_accrual": True
                }
                
                # Calculate daily rate based on assumption that last check covered 14 days
                # This normalizes the accrual regardless of pay frequency
                for key in ytd_accumulators:
                    last_check_amount = safe_round(last_record.get(key, 0))
                    
                    # Daily Rate
                    daily_rate = last_check_amount / 14.0
                    
                    # Projected Amount for remaining days
                    accrued_amount = safe_round(daily_rate * days_remaining)
                    
                    accrual_row[key] = accrued_amount
                    
                    # Update YTD Totals
                    ytd_accumulators[key] = safe_round(ytd_accumulators[key] + accrued_amount)
                    accrual_row[f"YTD_{key}"] = ytd_accumulators[key]
                
                processed_rows.append(accrual_row)

        # Construct Report
        report_doc = {
            "document_id": f"YTD-{target_year}-{emp_id}", 
            "doc_type": f"EMPLOYEE EARNINGS RECORD - {target_year}",
            "company_name": "ACME CORPORATION",
            "run_date": datetime.now().strftime("%Y-%m-%d"),
            "employee_name": emp_name,
            "employee_id": emp_id,
            "department": department,
            "fiscal_year": target_year,
            "rows": processed_rows,
            "final_totals": ytd_accumulators,
            "period_count": len(processed_rows)
        }
        
        employee_reports.append(report_doc)

    # Output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(employee_reports, f, indent=2)

    print(f"Successfully generated {len(employee_reports)} employee YTD reports in '{output_file}'.")

if __name__ == "__main__":
    process_employee_ytd(target_year=2024)