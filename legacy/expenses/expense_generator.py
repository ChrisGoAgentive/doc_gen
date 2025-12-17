import os
from jinja2 import Environment, FileSystemLoader
# Import the new utility
from utils.data_utils import DataFormatter

class HTMLGenerator:
    """
    A generic class to render HTML from Jinja2 templates.
    Now equipped with QOL filters for data formatting.
    """
    def __init__(self, template_dir='templates'):
        """
        Initialize with the directory containing your .html templates.
        """
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
        
        # --- REGISTER QOL FILTERS ---
        # This allows templates to use pipes, e.g., {{ amount | currency }}
        self.env.filters['currency'] = DataFormatter.format_currency
        self.env.filters['fmt_date'] = DataFormatter.format_date
        self.env.filters['phone'] = DataFormatter.format_phone

    def render(self, template_name, context):
        """
        Renders a single template with the provided dictionary context.
        Returns: String (HTML)
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            print(f"Error rendering {template_name}: {e}")
            return None

    def render_to_file(self, template_name, context, output_path):
        """
        Renders content and saves it directly to a file.
        """
        content = self.render(template_name, context)
        if content:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False