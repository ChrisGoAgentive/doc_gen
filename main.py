import os
import json
import random
from generator import DocumentGenerator

# --- ReportLab Imports ---
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
# -------------------------

def ensure_directories():
    """Create necessary directories if they don't exist."""
    if not os.path.exists('output'):
        os.makedirs('output')
    # Create specific output folder for invoices
    if not os.path.exists('output/invoices'):
        os.makedirs('output/invoices')
    if not os.path.exists('templates'):
        os.makedirs('templates')
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')

def create_pdf_reportlab(filepath, data):
    """
    Generates a PDF document directly from structured data using ReportLab.
    This replaces the HTML rendering step and eliminates the wkhtmltopdf dependency.
    """
    try:
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Custom Styles
        style_title = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, spaceAfter=20)
        style_h2 = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=16, spaceBefore=10, spaceAfter=10)
        style_normal = styles['Normal']

        # Title
        story.append(Paragraph(data.get("title", "DOCUMENT"), style_title))
        story.append(Spacer(1, 0.5 * inch))

        # Header/Metadata
        story.append(Paragraph(f"<b>Document ID:</b> {data.get('document_id', 'N/A')}", style_normal))
        story.append(Paragraph(f"<b>Date:</b> {data.get('date', 'N/A')}", style_normal))
        story.append(Spacer(1, 0.25 * inch))

        # Sender/Recipient Details
        sender = data.get('sender', {})
        recipient = data.get('recipient', {})
        
        details_data = [
            [
                Paragraph("<b>From:</b>", style_h2),
                Paragraph("<b>Bill To:</b>", style_h2)
            ],
            [
                Paragraph(f"{sender.get('company', '')}<br/>{sender.get('address', '')}", style_normal),
                Paragraph(f"{recipient.get('name', '')}<br/>{recipient.get('company', '')}<br/>{recipient.get('address', '')}", style_normal)
            ]
        ]

        details_table = Table(details_data, colWidths=[3.0 * inch, 3.0 * inch])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 0.5 * inch))

        # Line Items Table
        table_data = [["Description", "Qty", "Unit Price", "Total"]]
        
        for item in data.get('items', []):
            table_data.append([
                item.get('description', 'N/A'),
                item.get('quantity', 0),
                f"${item.get('unit_price', 0.00):.2f}",
                f"${item.get('total', 0.00):.2f}"
            ])

        item_table = Table(table_data, colWidths=[3.5*inch, 0.5*inch, 1*inch, 1*inch])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 0.5 * inch))

        # Totals
        totals_data = [
            ["Subtotal:", f"${data.get('subtotal', 0.00):.2f}"],
            ["Tax:", f"${data.get('tax', 0.00):.2f}"],
            ["GRAND TOTAL:", f"${data.get('grand_total', 0.00):.2f}"],
        ]
        
        totals_table = Table(totals_data, colWidths=[1.5 * inch, 1.5 * inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('LINEBELOW', (0, 1), (-1, 1), 1, colors.black),
            ('BACKGROUND', (0, 2), (-1, 2), colors.lightgrey),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        # Use a nested table structure to align totals to the right side of the page
        totals_container = Table([['', totals_table]], colWidths=[4.0 * inch, 3.0 * inch])
        totals_container.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
        story.append(totals_container)
        story.append(Spacer(1, 0.5 * inch))

        # Notes
        notes = data.get('notes')
        if notes:
             story.append(Paragraph(f"<b>Notes:</b> {notes}", style_normal))

        # Build the PDF
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error generating ReportLab PDF: {e}")
        return False

def main():
    ensure_directories()
    doc_gen = DocumentGenerator(template_dir='templates')

    print("--- Starting Document Generation (using ReportLab) ---")

    print("\n2. Generating Invoice from JSON...")
    json_path = 'data/invoice.json'
    
    if os.path.exists(json_path):
        real_data = doc_gen.load_data_from_json(json_path)
        
        if real_data:
            # We use the structured data directly
            filename_json = f"output/invoices/{real_data.get('document_id', 'unknown')}.pdf"
            
            if create_pdf_reportlab(filename_json, real_data):
                print(f"   Saved PDF: {filename_json}")
            else:
                print("   Failed to generate JSON-based PDF.")
    else:
        print(f"   Warning: {json_path} not found. Please create it to test JSON injection.")

if __name__ == "__main__":
    main()