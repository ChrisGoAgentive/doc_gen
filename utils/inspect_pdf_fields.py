import os
from pypdf import PdfReader

def inspect_pdf_fields(pdf_path):
    """
    Reads a fillable PDF and prints the field names (keys) and their current values.
    Use this to determine the mapping keys for your generation script.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    reader = PdfReader(pdf_path)
    fields = reader.get_fields()

    print(f"--- Inspetion Report for: {os.path.basename(pdf_path)} ---")
    print(f"{'Field Name':<50} | {'Current Value'}")
    print("-" * 80)

    if fields:
        for field_name, value in fields.items():
            # Handle cases where value might be None or a complex object
            val_str = str(value.get('/V', '')) if value else ''
            print(f"{field_name:<50} | {val_str}")
    else:
        print("No form fields found. Is this a fillable PDF?")

if __name__ == "__main__":
    # Point this to your uploaded 1099-R template
    pdf_path = "templates/f1099r.pdf" 
    inspect_pdf_fields(pdf_path)