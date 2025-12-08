import json
import os
import random
import hashlib
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker
fake = Faker()

def get_deterministic_seed(input_string):
    """
    Converts a string (like a UUID) into an integer seed.
    This ensures that for the same ID, we always generate the same 'random' data.
    """
    return int(hashlib.sha256(input_string.encode('utf-8')).hexdigest(), 16) % (10 ** 8)

def generate_documents_from_record(record):
    """
    Core Logic: Takes a single expense ledger record (source of truth) and 
    deterministically creates the full data structures for PO, RR, and Invoice.
    """
    
    # 1. Deterministic Seeding
    # This ensures that if you run this script tomorrow, the "Random" 
    # vendor address for this specific transaction will be exactly the same.
    seed = get_deterministic_seed(record.get("Journal_Entry_ID", "default"))
    random.seed(seed)
    Faker.seed(seed) # Global faker seed for this iteration
    
    # Local faker instance for safety
    local_fake = Faker()
    local_fake.seed_instance(seed)

    # 2. Parse Dates (The Timeline)
    # Format: 2025-03-25T00:00:00.000
    try:
        date_str = record["Transaction_Date"].split('T')[0]
        invoice_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        invoice_date_obj = datetime.now()

    # Timeline Logic: 
    # PO Created (10-20 days before) -> Goods Received (2-5 days before) -> Invoice Date (Transaction Date)
    days_before_po = random.randint(10, 20)
    days_before_rr = random.randint(2, 5)
    
    po_date_obj = invoice_date_obj - timedelta(days=days_before_po)
    rr_date_obj = invoice_date_obj - timedelta(days=days_before_rr)

    # 3. Establish Entities
    # We generate the "Fake" details here, once, and save them to the JSON.
    vendor = {
        "company": record["Vendor_Name"],
        "address": local_fake.address().replace('\n', ', '),
        "email": f"billing@{record['Vendor_Name'].split(' ')[0].replace(',', '').lower()}.com",
        "vendor_id": record["Vendor_ID"]
    }
    
    client = {
        "company": "Your Client Corp", 
        "address": local_fake.address().replace('\n', ', '),
        "name": f"User {record['User_ID']}"
    }

    # 4. Create Line Items
    # strictly match the audit amounts from the ledger
    
    # We prioritize the Total Amount as the anchor (Total - Tax = Net)
    # This ensures the Invoice Total matches the Ledger Total exactly.
    total_amount = record["Total_Amount"]
    tax_amount = record["Tax_Amount"]
    net_amount = round(total_amount - tax_amount, 2)

    items = [{
        "description": record["GL_Account_Name"],
        "quantity": 1,
        "unit_price": net_amount,
        "total": net_amount
    }]

    subtotal = net_amount
    # tax_amount is defined above
    # total_amount is defined above

    # 5. Generate Document IDs
    # Base them on the Journal ID so they are traceable back to the ledger
    base_id = record["Journal_Entry_ID"][:8].upper()
    po_id = f"PO-{base_id}"
    rr_id = f"REC-{base_id}"
    inv_id = f"INV-{base_id}"

    # 6. Build Purchase Order Data
    po = {
        "doc_type": "PURCHASE ORDER",
        "document_id": po_id,
        "date": po_date_obj.strftime("%Y-%m-%d"),
        "sender": client,    # Buyer
        "recipient": vendor, # Seller
        "items": items,
        "subtotal": subtotal,
        "tax": tax_amount,
        "grand_total": total_amount,
        "notes": f"Authorized by {record['Approver_ID']}. GL: {record['GL_Account_Code']}"
    }

    # 7. Build Receiving Report Data
    rr = {
        "doc_type": "RECEIVING REPORT",
        "document_id": rr_id,
        "ref_id": po_id,
        "date": rr_date_obj.strftime("%Y-%m-%d"),
        "sender": vendor,     # Shipped From
        "recipient": client,  # Received At
        "items": items,
        "subtotal": total_amount - tax_amount,
        "tax": tax_amount,
        "grand_total": total_amount,
        "notes": "Received in full. Condition: Good."
    }

    # 8. Build Invoice Data
    inv = {
        "doc_type": "INVOICE",
        "document_id": inv_id,
        "ref_id": po_id,
        "date": invoice_date_obj.strftime("%Y-%m-%d"),
        "sender": vendor,     # Billed From
        "recipient": client,  # Billed To
        "items": items,
        "subtotal": subtotal,
        "tax": tax_amount,
        "grand_total": total_amount,
        "notes": f"Payment Terms: Net 30. GL: {record['GL_Account_Code']}"
    }

    return po, rr, inv

def process_ledger_file(input_file='data/expenses.json'):
    if not os.path.exists(input_file):
        print(f"Error: Source file '{input_file}' not found.")
        return

    print(f"--- Processing Ledger: {input_file} ---")
    
    with open(input_file, 'r') as f:
        expenses = json.load(f)
        
    print(f"Found {len(expenses)} expense entries.")
    
    all_pos = []
    all_rrs = []
    all_invs = []
    
    for expense in expenses:
        po, rr, inv = generate_documents_from_record(expense)
        all_pos.append(po)
        all_rrs.append(rr)
        all_invs.append(inv)
        
    if not os.path.exists('data'):
        os.makedirs('data')
        
    # Save the FULLY FORMED data. 
    # The Document Generator will just read these and print them.
    
    with open('data/purchase_orders.json', 'w') as f:
        json.dump(all_pos, f, indent=2)
    print(f"1. Generated data/purchase_orders.json ({len(all_pos)} docs)")
        
    with open('data/receiving_reports.json', 'w') as f:
        json.dump(all_rrs, f, indent=2)
    print(f"2. Generated data/receiving_reports.json ({len(all_rrs)} docs)")

    with open('data/invoices.json', 'w') as f:
        json.dump(all_invs, f, indent=2)
    print(f"3. Generated data/invoices.json ({len(all_invs)} docs)")

if __name__ == "__main__":
    process_ledger_file()