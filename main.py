import os
import json
from generator import DocumentGenerator

def ensure_directories():
    """Create necessary directories if they don't exist."""
    paths = [
        'output', 'output/html', 'output/pdfs',
        'output/pdfs/invoices', 'output/pdfs/purchase_orders', 'output/pdfs/receiving_reports',
        'output/html/invoices', 'output/html/purchase_orders', 'output/html/receiving_reports',
        'templates', 'data'
    ]
    for p in paths:
        if not os.path.exists(p):
            os.makedirs(p)

def process_bulk_files(doc_gen, json_filename, template_name, type_folder):
    """
    Reads a JSON file (Source of Truth) and instructs doc_gen to print it.
    """
    json_path = f'data/{json_filename}'
    if not os.path.exists(json_path):
        print(f"Skipping {json_filename} (File not found)")
        return

    print(f"\n--- Printing from Source: {json_filename} ---")
    with open(json_path, 'r') as f:
        docs = json.load(f)

    print(f"Found {len(docs)} documents.")
    
    for doc in docs:
        doc_id = doc.get('document_id', 'unknown')
        
        # 1. Print HTML Preview
        html_content = doc_gen.render_html_template(template_name, doc)
        if html_content:
            html_path = f"output/html/{type_folder}/{doc_id}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        # 2. Print PDF
        pdf_path = f"output/pdfs/{type_folder}/{doc_id}.pdf"
        doc_gen.render_pdf(doc, pdf_path)
        
    print(f"Completed {type_folder}: {len(docs)} HTML files and {len(docs)} PDFs created.")

def main():
    ensure_directories()
    
    # Initialize the Printer
    doc_gen = DocumentGenerator(template_dir='templates')

    # Run the Print Jobs
    process_bulk_files(doc_gen, 'invoices.json', 'invoice.html', 'invoices')
    process_bulk_files(doc_gen, 'purchase_orders.json', 'purchase_order.html', 'purchase_orders')
    process_bulk_files(doc_gen, 'receiving_reports.json', 'receiving_report.html', 'receiving_reports')

    print("\n--- All Operations Complete ---")
    print("Check 'output/pdfs/' for your final audit documents.")

if __name__ == "__main__":
    main()