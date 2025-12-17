import os
import sys
import argparse
import random

# Fix path to find modules in root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from expenses.expense_generator import HTMLGenerator
from pdf_engine import PDFGenerator
from utils.data_utils import DataLoader
from utils.scan_fx import ScanFX

# Try importing num2words
try:
    from num2words import num2words
    NUM2WORDS_AVAIL = True
except ImportError:
    NUM2WORDS_AVAIL = False
    print("Warning: 'num2words' not found. Check amounts will be generic.")

def get_amount_text(amount):
    """
    Converts 123.45 to 'ONE HUNDRED TWENTY-THREE AND 45/100'.
    """
    try:
        total = float(amount)
        dollars = int(total)
        cents = int(round((total - dollars) * 100))
        
        if NUM2WORDS_AVAIL:
            words = num2words(dollars, lang='en').upper().replace('-', ' ')
        else:
            words = f"{dollars} DOLLARS"
            
        return f"{words} AND {cents:02d}/100"
    except Exception:
        return "INVALID AMOUNT"

def main():
    parser = argparse.ArgumentParser(description="Check Generator with Scan FX")
    parser.add_argument('--data', required=True, help="JSON file with check data")
    parser.add_argument('--out', default='output/checks', help="Output directory")
    args = parser.parse_args()

    # 1. Setup Generators
    # Template dir is relative to the root, so '../templates' if we were running from here,
    # but we will likely run from root or handle paths carefully. 
    # HTMLGenerator expects 'templates' by default.
    html_gen = HTMLGenerator(template_dir='templates')
    pdf_gen = PDFGenerator()
    
    checks_data = DataLoader.load(args.data)
    
    if not checks_data:
        print("No check data found.")
        return

    os.makedirs(args.out, exist_ok=True)
    
    print(f"--- Generating {len(checks_data)} Checks ---")
    print(f"Output: {args.out}")

    success_count = 0
    for doc in checks_data:
        check_num = doc.get('check_number', '0000')
        doc_id = f"CHECK_{check_num}"
        
        # A. Prepare Data (Add Text Amount)
        if 'amount_text' not in doc and 'amount' in doc:
            doc['amount_text'] = get_amount_text(doc['amount'])
            
        # B. Render HTML
        # We assume main.py style where template dir is root/templates
        html_content = html_gen.render('check_template.html', doc)
        
        if html_content:
            # C. Generate Clean PDF (Intermediate)
            clean_pdf_path = os.path.join(args.out, f"{doc_id}_clean.pdf")
            
            if pdf_gen.render_html_to_pdf(html_content, clean_pdf_path):
                
                # D. Apply Scan Effects
                final_pdf_path = os.path.join(args.out, f"{doc_id}.pdf")
                
                # If ScanFX fails (missing lib), we just keep the clean one or rename it
                if ScanFX.apply_scan_effect(clean_pdf_path, final_pdf_path):
                    # Remove the clean one to save space/confusion
                    os.remove(clean_pdf_path)
                    print(f"Generated Scanned: {doc_id}.pdf")
                else:
                    # Fallback: keep clean PDF if scan fx fails
                    os.rename(clean_pdf_path, final_pdf_path)
                    print(f"Generated Clean (Scan FX Skipped): {doc_id}.pdf")
                
                success_count += 1
            else:
                print(f"Failed to render PDF for {doc_id}")
        else:
            print(f"Failed to render HTML template for {doc_id}")

    print(f"--- Complete. Generated {success_count} checks. ---")

if __name__ == "__main__":
    main()