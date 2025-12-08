import argparse
import json
import os
import sys
import shutil
from expenses.expense_generator import HTMLGenerator
from pdf_engine import PDFGenerator

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
    parser = argparse.ArgumentParser(description="Financial PDF Generator")
    
    # Required Arguments
    parser.add_argument('--data', required=True, help="Path to JSON data file")
    parser.add_argument('--template', required=True, help="Name of the Jinja2 template to use (e.g., invoice.html)")
    
    # Optional Arguments
    parser.add_argument('--out', default='output', help="Output directory")
    parser.add_argument('--id-key', default='document_id', help="JSON key to use for filenames")
    
    args = parser.parse_args()

    # 1. Setup Generators
    # HTMLGenerator handles the design (Jinja2)
    html_gen = HTMLGenerator(template_dir='templates')
    # PDFGenerator handles the format conversion (HTML String -> PDF)
    pdf_gen = PDFGenerator()
    
    data_source = load_data(args.data)
    if not data_source:
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(args.out, exist_ok=True)

    # Optional: Copy the source data to output for reference
    try:
        dest_path = os.path.join(args.out, os.path.basename(args.data))
        shutil.copy2(args.data, dest_path)
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
        
        # Define Output Path
        pdf_out_path = os.path.join(args.out, f"{safe_id}.pdf")
        
        # Step A: Render Template to HTML String (In-Memory)
        html_content = html_gen.render(args.template, doc)
        
        if html_content:
            # Step B: Convert HTML String to PDF File
            if pdf_gen.render_html_to_pdf(html_content, pdf_out_path):
                success_count += 1
            else:
                print(f"Failed to convert {safe_id} to PDF.")
        else:
            print(f"Failed to render template for {safe_id}")

    print(f"--- Complete. Generated {success_count} PDF files. ---")

if __name__ == "__main__":
    main()