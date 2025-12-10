import argparse
import os
import sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, TextStringObject

def create_debug_pdf_map(input_pdf_path, output_dir):
    """
    Reads a PDF form and creates a 'debug' version where every text field
    is filled with its own internal field name.
    
    Crucial for mapping complex XFA or unknown PDF forms.
    """
    if not os.path.exists(input_pdf_path):
        print(f"Error: Input file not found at {input_pdf_path}")
        sys.exit(1)

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filename = os.path.basename(input_pdf_path)
    output_path = os.path.join(output_dir, f"debug_map_{filename}")

    print(f"--- Generating Debug Map ---")
    print(f"Input:  {input_pdf_path}")
    print(f"Output: {output_path}")

    try:
        reader = PdfReader(input_pdf_path)
        writer = PdfWriter()

        # 1. Copy Pages
        writer.append_pages_from_reader(reader)

        # 2. Copy Root AcroForm Dictionary (Required for fields to work)
        if "/AcroForm" in reader.root_object:
            writer.root_object[NameObject("/AcroForm")] = reader.root_object["/AcroForm"]

        # 3. Clean up AcroForm (Fix Adobe/Viewer Compatibility)
        if "/AcroForm" in writer.root_object:
            acroform = writer.root_object["/AcroForm"]
            
            # Remove XFA: Forces the viewer to use the standard fields we are about to edit
            if "/XFA" in acroform:
                print(" - Removing XFA dictionary to ensure editability.")
                del acroform["/XFA"]
            
            # Enable NeedAppearances: Forces the viewer to render the text we write
            acroform[NameObject("/NeedAppearances")] = BooleanObject(True)

        # 4. Iterate and Fill Fields with their Own Names
        filled_count = 0
        
        # Iterate through all pages
        for page in writer.pages:
            if "/Annots" in page:
                for annot in page["/Annots"]:
                    annot_obj = annot.get_object()
                    
                    # Ensure it is a form widget
                    if "/Subtype" in annot_obj and annot_obj["/Subtype"] == "/Widget":
                        field_name = annot_obj.get("/T")
                        
                        if field_name:
                            # Handle Checkboxes/Buttons
                            if annot_obj.get("/FT") == "/Btn":
                                # Mark as Checked/Yes so we can see where it is
                                annot_obj[NameObject("/V")] = NameObject("/Yes")
                                annot_obj[NameObject("/AS")] = NameObject("/Yes")
                            else:
                                # Text Fields: Write the Field Name into the box
                                annot_obj[NameObject("/V")] = TextStringObject(str(field_name))
                            
                            filled_count += 1

        print(f" - Mapped {filled_count} fields.")

        # 5. Write Output
        with open(output_path, "wb") as f:
            writer.write(f)
            
        print(f"Success! Open '{output_path}' to see the field names.")

    except Exception as e:
        print(f"Error generating debug map: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a PDF where fields are filled with their own names.")
    parser.add_argument("input_pdf", help="Path to the source PDF form")
    parser.add_argument("--out", default="output", help="Directory to save the debug PDF")
    
    args = parser.parse_args()
    
    create_debug_pdf_map(args.input_pdf, args.out)