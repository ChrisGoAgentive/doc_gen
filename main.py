import argparse
import json
import os
import sys
import shutil
from expenses.expense_generator import HTMLGenerator
from expenses.expense_engine import ExpensePDFGenerator

def load_data(filepath):
    if not os.path.exists(filepath):
        print(f"Error: Data file '{filepath}' not found.")
        return None
    with open(filepath, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Generic Document Generator")
    
    # Required Arguments
    parser.add_argument('--data', required=True, help="Path to JSON data file")
    parser.add_argument('--template', required=True, help="Name of the HTML template (e.g., invoice.html)")
    
    # Optional Arguments
    parser.add_argument('--out', default='output', help="Base output directory")
    parser.add_argument('--id-key', default='document_id', help="JSON key to use for filenames (default: document_id)")
    parser.add_argument('--pdf', action='store_true', help="Generate PDFs (requires Expense schema)")
    
    args = parser.parse_args()

    # 1. Setup
    html_gen = HTMLGenerator(template_dir='templates')
    pdf_gen = ExpensePDFGenerator() if args.pdf else None
    
    data_source = load_data(args.data)
    if not data_source:
        sys.exit(1)

    # Copy the reference data file to the output directory
    try:
        os.makedirs(args.out, exist_ok=True)
        dest_path = os.path.join(args.out, os.path.basename(args.data))
        shutil.copy2(args.data, dest_path)
        print(f"Reference file copied to: {dest_path}")
    except Exception as e:
        print(f"Warning: Failed to copy reference file: {e}")

    # Ensure we treat single objects as a list for consistent processing
    documents = data_source if isinstance(data_source, list) else [data_source]
    
    print(f"--- Processing {len(documents)} documents ---")
    print(f"Template: {args.template}")
    print(f"Output:   {args.out}")

    success_count = 0

    # 2. Processing Loop
    for doc in documents:
        # Determine Filename
        doc_id = doc.get(args.id_key, 'unknown_id')
        safe_id = "".join([c for c in doc_id if c.isalnum() or c in ('-','_')])
        
        # Paths
        html_out_path = os.path.join(args.out, 'html', f"{safe_id}.html")
        
        # Render HTML
        if html_gen.render_to_file(args.template, doc, html_out_path):
            success_count += 1
            
        # Render PDF (Optional & Schema Dependent)
        if args.pdf:
            pdf_out_path = os.path.join(args.out, 'pdf', f"{safe_id}.pdf")
            pdf_gen.render(doc, pdf_out_path)

    print(f"--- Complete. Generated {success_count} HTML files. ---")

if __name__ == "__main__":
    main()