import os
from jinja2 import Environment, FileSystemLoader

class HTMLGenerator:
    """
    A generic class to render HTML from Jinja2 templates.
    This class is agnostic to the data structure (Invoice, Report, Letter, etc.).
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