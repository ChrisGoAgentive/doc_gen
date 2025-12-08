import logging

# Try importing WeasyPrint, which is excellent for HTML->PDF
# You will need to install it: pip install weasyprint
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

class PDFGenerator:
    """
    Generic class to convert HTML content to PDF.
    """
    
    def render_html_to_pdf(self, html_content, output_path):
        """
        Takes an HTML string and saves it as a PDF.
        """
        if not WEASYPRINT_AVAILABLE:
            print("Error: 'weasyprint' library not found.")
            print("Please run: pip install weasyprint")
            return False
        
        try:
            # WeasyPrint converts the HTML string directly to a PDF file
            HTML(string=html_content).write_pdf(output_path)
            return True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False