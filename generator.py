import os
import json
import random
from datetime import datetime
from faker import Faker
from jinja2 import Environment, FileSystemLoader

class DocumentGenerator:
    def __init__(self, template_dir='templates'):
        self.fake = Faker()
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )

    def render_template(self, template_name, data):
        try:
            template = self.env.get_template(template_name)
            return template.render(**data)
        except Exception as e:
            print(f"Error rendering template {template_name}: {e}")
            return None
            
    def load_data_from_json(self, json_filepath):
        """
        Loads structured data from a JSON file.
        """
        try:
            with open(json_filepath, 'r') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            print(f"Error: Data file not found at {json_filepath}")
            return None
        except json.JSONDecodeError:
            print(f"Error: Failed to decode JSON from {json_filepath}")
            return None

    def generate_invoice_data(self, num_items=5):
        """
        Generates a dictionary of fake data suitable for an invoice.
        """
        items = []
        total = 0.0
        
        for _ in range(num_items):
            # Create realistic looking line items
            qty = random.randint(1, 10)
            unit_price = round(random.uniform(10.0, 500.0), 2)
            line_total = round(qty * unit_price, 2)
            
            items.append({
                "description": self.fake.catch_phrase(),
                "quantity": qty,
                "unit_price": unit_price,
                "total": line_total
            })
            total += line_total

        return {
            "title": "INVOICE",
            "document_id": f"INV-{self.fake.random_number(digits=6)}",
            "date": datetime.now().strftime("%B %d, %Y"),
            "due_date": self.fake.future_date(end_date="+30d").strftime("%B %d, %Y"),
            "sender": {
                "company": self.fake.company(),
                "address": self.fake.address().replace('\n', ', '),
                "email": self.fake.company_email()
            },
            "recipient": {
                "name": self.fake.name(),
                "company": self.fake.company(),
                "address": self.fake.address().replace('\n', ', ')
            },
            "items": items,
            "subtotal": round(total, 2),
            "tax": round(total * 0.08, 2), # Mock 8% tax
            "grand_total": round(total * 1.08, 2),
            "notes": self.fake.text(max_nb_chars=100)
        }
    

    def generate_purchase_order_data(self):
        """
        Example stub for next document type.
        """
        pass