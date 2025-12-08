import json
from jinja2 import Environment, FileSystemLoader

# --- ReportLab Imports ---
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

class DocumentGenerator:
    """
    The Printer. 
    Responsibility: Take valid data and format it into HTML or PDF.
    Does NOT contain business logic or data creation logic.
    """
    def __init__(self, template_dir='templates'):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )

    def render_html_template(self, template_name, data):
        """
        Renders a Jinja2 HTML template.
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**data)
        except Exception as e:
            print(f"Error rendering HTML template {template_name}: {e}")
            return None

    def render_pdf(self, data, filepath):
        """
        Generates a PDF using ReportLab.
        """
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Dynamic Styling based on Doc Type
            doc_type = data.get("doc_type", data.get("title", "DOCUMENT"))
            theme_color = colors.black
            if "INVOICE" in doc_type.upper(): theme_color = colors.navy
            elif "PURCHASE" in doc_type.upper(): theme_color = colors.steelblue
            elif "RECEIVING" in doc_type.upper(): theme_color = colors.forestgreen

            # Styles
            style_title = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, spaceAfter=20, textColor=theme_color)
            style_h2 = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=14, spaceBefore=10, textColor=theme_color)
            style_normal = styles['Normal']

            # 1. Title
            story.append(Paragraph(doc_type, style_title))
            
            # 2. Meta Data (ID, Date)
            meta_data = [
                ["ID:", data.get('document_id', 'N/A')],
                ["Date:", data.get('date', 'N/A')],
                ["Ref:", data.get('ref_id', '-')]
            ]
            t_meta = Table(meta_data, colWidths=[1*inch, 2*inch], hAlign='LEFT')
            t_meta.setStyle(TableStyle([('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold')]))
            story.append(t_meta)
            story.append(Spacer(1, 0.3 * inch))

            # 3. Addresses
            sender = data.get('sender', {})
            recipient = data.get('recipient', {})
            
            details_data = [
                [Paragraph("<b>From:</b>", style_h2), Paragraph("<b>To:</b>", style_h2)],
                [
                    Paragraph(f"{sender.get('company', '')}<br/>{sender.get('address', '')}<br/>{sender.get('name', '')}", style_normal),
                    Paragraph(f"{recipient.get('company', '')}<br/>{recipient.get('address', '')}<br/>{recipient.get('name', '')}", style_normal)
                ]
            ]

            details_table = Table(details_data, colWidths=[3.5 * inch, 3.5 * inch])
            details_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            story.append(details_table)
            story.append(Spacer(1, 0.5 * inch))

            # 4. Line Items
            table_data = [["Description", "Qty", "Unit Price", "Total"]]
            for item in data.get('items', []):
                table_data.append([
                    item.get('description', 'N/A'),
                    str(item.get('quantity', 0)),
                    f"${item.get('unit_price', 0.00):.2f}",
                    f"${item.get('total', 0.00):.2f}"
                ])

            item_table = Table(table_data, colWidths=[4*inch, 0.5*inch, 1*inch, 1*inch])
            item_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), theme_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ]))
            story.append(item_table)
            story.append(Spacer(1, 0.5 * inch))

            # 5. Totals
            if data.get('grand_total'):
                totals_data = [
                    ["Subtotal:", f"${data.get('subtotal', 0.00):.2f}"],
                    ["Tax:", f"${data.get('tax', 0.00):.2f}"],
                    ["TOTAL:", f"${data.get('grand_total', 0.00):.2f}"],
                ]
                totals_table = Table(totals_data, colWidths=[1.5 * inch, 1.5 * inch])
                totals_table.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                    ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
                    ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),
                    ('TEXTCOLOR', (0, 2), (-1, 2), theme_color),
                ]))
                t_container = Table([['', totals_table]], colWidths=[4.5*inch, 3*inch])
                story.append(t_container)

            # 6. Notes
            notes = data.get('notes')
            if notes:
                 story.append(Spacer(1, 0.3 * inch))
                 story.append(Paragraph(f"<b>Notes/Auth:</b> {notes}", style_normal))

            doc.build(story)
            return True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False