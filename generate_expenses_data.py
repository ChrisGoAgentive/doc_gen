import json
import csv
import random
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

def generate_line_items(num_items=3):
    items = []
    total = 0.0
    
    for _ in range(num_items):
        qty = random.randint(1, 20)
        unit_price = round(random.uniform(10.0, 500.0), 2)
        amount = round(qty * unit_price, 2)
        
        item = {
            "description": fake.catch_phrase(),
            "quantity": qty,
            "unit_price": unit_price,
            "amount": amount,
            "sku": fake.bothify(text='??-####')
        }
        items.append(item)
        total += amount
        
    return items, total

def generate_invoices(num_records=20):
    invoices = []
    
    for _ in range(num_records):
        invoice_date = fake.date_between(start_date='-90d', end_date='today')
        due_date = invoice_date + timedelta(days=30)
        
        line_items, subtotal = generate_line_items(random.randint(1, 5))
        tax_rate = 0.08
        tax = round(subtotal * tax_rate, 2)
        total = round(subtotal + tax, 2)
        
        inv_num = fake.bothify(text='INV-####-???')
        
        invoice = {
            "id": inv_num,  # vital for main.py to identify the record
            "invoice_number": inv_num,
            "date": invoice_date.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "vendor": {
                "name": fake.company(),
                "address": fake.street_address(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "zip": fake.zipcode(),
                "phone": fake.phone_number(),
                "email": fake.company_email()
            },
            "bill_to": {
                "company": "TechFlow Solutions",
                "address": "123 Tech Blvd",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94105"
            },
            "items": line_items,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "notes": fake.sentence(),
            "status": random.choice(["Paid", "Pending", "Overdue"])
        }
        invoices.append(invoice)
        
    return invoices

def generate_purchase_orders(num_records=20):
    purchase_orders = []
    
    for _ in range(num_records):
        po_date = fake.date_between(start_date='-60d', end_date='today')
        line_items, subtotal = generate_line_items(random.randint(1, 8))
        
        po_num = fake.bothify(text='PO-####-???')
        
        po = {
            "id": po_num, # vital for main.py
            "po_number": po_num,
            "date": po_date.strftime("%Y-%m-%d"),
            "vendor": {
                "name": fake.company(),
                "contact": fake.name(),
                "address": fake.address().replace('\n', ', ')
            },
            "ship_to": {
                "company": "TechFlow Solutions Warehouse",
                "address": "456 Logistics Way",
                "city": "Hayward",
                "state": "CA",
                "zip": "94544"
            },
            "shipping_method": random.choice(["Ground", "Air", "Sea", "Express"]),
            "items": line_items,
            "total_amount": subtotal,
            "approved_by": fake.name(),
            "status": random.choice(["Issued", "Received", "Closed"])
        }
        purchase_orders.append(po)
        
    return purchase_orders

def generate_receiving_reports(purchase_orders):
    receiving_reports = []
    
    # Generate a receiving report for a subset of POs
    selected_pos = random.sample(purchase_orders, k=int(len(purchase_orders) * 0.8))
    
    for po in selected_pos:
        received_date = datetime.strptime(po["date"], "%Y-%m-%d") + timedelta(days=random.randint(2, 14))
        
        # Simulate receiving items (sometimes partial, sometimes full)
        received_items = []
        for item in po["items"]:
            qty_ordered = item["quantity"]
            # 90% chance of full receipt, 10% chance of partial/issue
            if random.random() > 0.1:
                qty_received = qty_ordered
                condition = "Good"
            else:
                qty_received = random.randint(0, qty_ordered)
                condition = random.choice(["Damaged", "Missing Parts", "Wrong Item"])
                
            received_items.append({
                "sku": item["sku"],
                "description": item["description"],
                "qty_ordered": qty_ordered,
                "qty_received": qty_received,
                "condition": condition
            })
            
        rec_num = fake.bothify(text='REC-####')
        
        report = {
            "id": rec_num, # vital for main.py
            "receipt_number": rec_num,
            "po_number": po["po_number"],
            "date_received": received_date.strftime("%Y-%m-%d"),
            "vendor": po["vendor"]["name"],
            "carrier": random.choice(["FedEx", "UPS", "DHL", "USPS", "Freight"]),
            "tracking_number": fake.bothify(text='TRK-################'),
            "items": received_items,
            "received_by": fake.name(),
            "comments": fake.sentence() if random.random() > 0.7 else ""
        }
        receiving_reports.append(report)
        
    return receiving_reports

def flatten_for_csv(data_list, record_type):
    """
    Flattens nested JSON data for CSV export.
    Since line items are lists, this function creates a row per line item.
    """
    flat_data = []
    
    for record in data_list:
        # Common fields based on record type
        base_record = {}
        items = []
        
        if record_type == "invoice":
            base_record = {
                "id": record["id"],
                "date": record["date"],
                "vendor": record["vendor"]["name"],
                "total": record["total"],
                "status": record["status"]
            }
            items = record["items"]
            
        elif record_type == "purchase_order":
            base_record = {
                "id": record["id"],
                "date": record["date"],
                "vendor": record["vendor"]["name"],
                "total": record["total_amount"],
                "status": record["status"]
            }
            items = record["items"]
            
        elif record_type == "receiving_report":
            base_record = {
                "id": record["id"],
                "ref_id": record["po_number"],
                "date": record["date_received"],
                "vendor": record["vendor"],
                "carrier": record["carrier"]
            }
            items = record["items"]
            
        # Create a row for each item
        for item in items:
            row = base_record.copy()
            if record_type == "receiving_report":
                row.update({
                    "item_sku": item.get("sku", ""),
                    "item_desc": item.get("description", ""),
                    "qty_primary": item.get("qty_received", 0), # received
                    "qty_secondary": item.get("qty_ordered", 0), # ordered
                    "condition": item.get("condition", "")
                })
            else:
                row.update({
                    "item_sku": item.get("sku", ""),
                    "item_desc": item.get("description", ""),
                    "qty": item.get("quantity", 0),
                    "unit_price": item.get("unit_price", 0),
                    "line_total": item.get("amount", 0)
                })
            flat_data.append(row)
            
    return flat_data

def main():
    print("Generating expenses data...")
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # 1. Invoices
    print("Generating Invoices...")
    invoices = generate_invoices(25)
    with open('data/invoices.json', 'w') as f:
        json.dump(invoices, f, indent=4)
    
    invoices_flat = flatten_for_csv(invoices, "invoice")
    if invoices_flat:
        with open('data/invoices.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=invoices_flat[0].keys())
            writer.writeheader()
            writer.writerows(invoices_flat)

    # 2. Purchase Orders
    print("Generating Purchase Orders...")
    pos = generate_purchase_orders(25)
    with open('data/purchase_orders.json', 'w') as f:
        json.dump(pos, f, indent=4)
    
    pos_flat = flatten_for_csv(pos, "purchase_order")
    if pos_flat:
        with open('data/purchase_orders.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=pos_flat[0].keys())
            writer.writeheader()
            writer.writerows(pos_flat)

    # 3. Receiving Reports (linked to POs)
    print("Generating Receiving Reports...")
    receiving_reports = generate_receiving_reports(pos)
    with open('data/receiving_reports.json', 'w') as f:
        json.dump(receiving_reports, f, indent=4)
    
    rr_flat = flatten_for_csv(receiving_reports, "receiving_report")
    if rr_flat:
        with open('data/receiving_reports.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rr_flat[0].keys())
            writer.writeheader()
            writer.writerows(rr_flat)
        
    print("Expenses data generation complete.")

if __name__ == "__main__":
    main()

# python main.py --data data/invoices.json --template invoice.html --out output/expenses
# python main.py --data data/purchase_orders.json --template purchase_order.html --out output/expenses
# python main.py --data data/receiving_reports.json --template receiving_report.html --out output/expenses