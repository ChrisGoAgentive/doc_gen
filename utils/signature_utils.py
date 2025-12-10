import os
import random
import io
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

class SignatureGenerator:
    """
    Utilities for generating simulated handwritten signatures on PDF pages using handwritten fonts.
    """

    @staticmethod
    def draw_signature(page, x, y, width, height, seed_text=None, font_path=None, color=(0, 0, 128)):
        """
        Generates a signature image using a specific font and inserts it into the PDF.
        
        Args:
            page (fitz.Page): The PyMuPDF page object to draw on.
            x, y (float): Top-left coordinates of the signature box.
            width, height (float): Dimensions of the signature box.
            seed_text (str): The name to sign.
            font_path (str): Path to the .ttf/.otf font file.
            color (tuple): RGB tuple (0-255) for ink color (default is navy blue).
        """
        if not seed_text:
            seed_text = "Signature"
            
        if not font_path or not os.path.exists(font_path):
            print(f"[SignatureGenerator] Warning: Font not found at {font_path}. Signature skipped.")
            return

        # 1. Setup Image Canvas (High Res for quality)
        # We use a scale factor (supersampling) to ensure the text looks crisp when downscaled onto the PDF
        scale = 3  
        img_w = int(width * scale)
        img_h = int(height * scale)
        
        # Create transparent background image
        img = Image.new('RGBA', (img_w, img_h), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # 2. Load and Fit Font
        # Start with a font size relative to height
        font_size = int(img_h * 0.8) 
        
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print(f"[SignatureGenerator] Error loading font: {e}")
            return

        # "Copy-fitting": Shrink font until text fits within the box
        # We leave a 10% margin horizontally, but a larger margin vertically 
        # to account for long descenders (g, y, j) in handwriting fonts.
        min_font_size = 10
        margin_w = img_w * 0.9
        margin_h = img_h * 0.7  # Increased safety margin (30% buffer vertical)
        
        while font_size > min_font_size:
            # Measure text size
            bbox = draw.textbbox((0, 0), seed_text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            
            if text_w < margin_w and text_h < margin_h:
                break
            
            font_size -= 5
            font = ImageFont.truetype(font_path, font_size)

        # 3. Draw Text Centered
        # Re-measure with final font
        bbox = draw.textbbox((0, 0), seed_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        # Center position
        text_x = (img_w - text_w) // 2
        text_y = (img_h - text_h) // 2
        
        # Vertical Adjustment: Shift text up slightly to protect descenders
        # Handwriting fonts often have deeper bottoms than tops.
        text_y -= int(img_h * 0.1) 
        
        # Ensure color is RGBA
        fill_color = color + (255,) # Add full opacity alpha channel
        
        draw.text((text_x, text_y), seed_text, font=font, fill=fill_color)
        
        # 4. Natural Variations
        # Add slight random rotation (-2 to 2 degrees) to look less mechanical
        if seed_text:
            random.seed(seed_text) # Deterministic rotation based on name
        
        angle = random.uniform(-2, 2)
        # Expand=True allows the image to grow if rotation pushes corners out
        img = img.rotate(angle, resample=Image.BICUBIC, expand=True)

        # 5. Insert into PDF
        # Convert PIL image to byte stream (PNG format preserves transparency)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        
        # Define the rectangle on the PDF page where the image goes
        rect = fitz.Rect(x, y, x + width, y + height)
        
        # Insert the image stream
        page.insert_image(rect, stream=img_bytes)