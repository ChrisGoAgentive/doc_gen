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

def process_payroll_journal(input_file='data/payroll_journal.json', output_file='data/payroll_registers.json'):
    """
    Reads the raw payroll journal, groups transactions by Pay Period,
    calculates totals with precise rounding, and outputs structured data.
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        journal_entries = json.load(f)

    print(f"Processing {len(journal_entries)} payroll transactions...")

    # Group entries by Pay Period
    grouped_data = defaultdict(list)
    for entry in journal_entries:
        # Sanitize the entry data immediately to ensure clean JSON output
        # We process these specific fields to ensure they are float format x.xx
        money_fields = [
            "Gross_Pay", "Tax_Fed", "Tax_State", "Tax_FICA", 
            "Benefit_Deduction", "Net_Pay"
        ]
        hour_fields = ["Hours_Reg", "Hours_OT"]

        for field in money_fields + hour_fields:
            if field in entry:
                entry[field] = safe_round(entry[field])

        grouped_data[entry['Pay_Period']].append(entry)

    registers = []

    # Process each Pay Period group into a document object
    for pay_period, entries in grouped_data.items():
        
        # Sort entries by Employee Name for the report
        entries.sort(key=lambda x: x['Employee_Name'])

        # Initialize Totals
        totals = {
            "Hours_Reg": 0.0,
            "Hours_OT": 0.0,
            "Gross_Pay": 0.0,
            "Tax_Fed": 0.0,
            "Tax_State": 0.0,
            "Tax_FICA": 0.0,
            "Benefit_Deduction": 0.0,
            "Net_Pay": 0.0
        }

        # Calculate Totals
        for entry in entries:
            totals["Hours_Reg"] += entry.get("Hours_Reg", 0)
            totals["Hours_OT"] += entry.get("Hours_OT", 0)
            totals["Gross_Pay"] += entry.get("Gross_Pay", 0)
            totals["Tax_Fed"] += entry.get("Tax_Fed", 0)
            totals["Tax_State"] += entry.get("Tax_State", 0)
            totals["Tax_FICA"] += entry.get("Tax_FICA", 0)
            totals["Benefit_Deduction"] += entry.get("Benefit_Deduction", 0)
            totals["Net_Pay"] += entry.get("Net_Pay", 0)

        # Final Rounding of Totals to prevent floating point artifacts (e.g. 100.00000001)
        for key in totals:
            totals[key] = safe_round(totals[key])

        # Get the Pay Date from the first entry in the group
        raw_date = entries[0].get("Pay_Date", datetime.now().isoformat())
        if "T" in raw_date:
            pay_date_display = raw_date.split("T")[0]
        else:
            pay_date_display = raw_date

        # Construct the Register Document
        register_doc = {
            "document_id": f"REG-{pay_period}",  # ID used for filename
            "doc_type": "PAYROLL REGISTER",
            "company_name": "ACME CORPORATION",
            "company_id": "CMP-99821",
            "pay_period": pay_period,
            "pay_date": pay_date_display,
            "run_date": datetime.now().strftime("%Y-%m-%d"),
            "entries": entries,
            "totals": totals,
            "count": len(entries)
        }
        
        registers.append(register_doc)

    # Output the structured data
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(registers, f, indent=2)

    print(f"Successfully generated {len(registers)} payroll registers in '{output_file}'.")

if __name__ == "__main__":
    process_payroll_journal()