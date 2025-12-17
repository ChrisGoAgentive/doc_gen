import os
import random
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
# Requires: pip install pdf2image
# Also requires poppler installed on the system path
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

class ScanFX:
    """
    Applies visual effects to PDFs to simulate a physical scanning process.
    """
    
    @staticmethod
    def apply_scan_effect(pdf_path, output_path, dpi=200):
        """
        Converts a PDF to an image, applies scan artifacts, and saves it back as PDF.
        """
        if not PDF2IMAGE_AVAILABLE:
            print("[ScanFX] Error: 'pdf2image' library not found. Cannot apply scan effects.")
            return False

        try:
            # 1. Convert PDF to Image (First page only for checks)
            # fmt='jpeg' avoids some transparency issues
            images = convert_from_path(pdf_path, dpi=dpi, fmt='jpeg')
            if not images:
                return False
            
            img = images[0].convert("RGB")
            
            # 2. Apply "Scan" Artifacts
            
            # A. Rotate slightly (Misalignment)
            angle = random.uniform(-1.0, 1.0)
            # fillcolor white to handle the corners appearing after rotation
            img = img.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))
            
            # B. Blur (Scanner optics not perfect)
            # A very slight blur helps merge sharp digital edges
            img = img.filter(ImageFilter.GaussianBlur(radius=0.4))
            
            # C. Noise / Grain (Paper texture and sensor noise)
            # Create a noise layer
            noise_array = np.random.normal(scale=8, size=(img.height, img.width, 3))
            # Add noise to image array
            img_array = np.array(img, dtype=float) + noise_array
            # Clip values to valid 0-255 range
            img_array = np.clip(img_array, 0, 255).astype('uint8')
            img = Image.fromarray(img_array)
            
            # D. Threshold / Contrast (Scanners often blow out highlights)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.4) 
            
            # E. Grayscale (Optional, often checks are scanned in B&W)
            # img = img.convert("L")

            # 3. Save back to PDF
            img.save(output_path, "PDF", resolution=dpi)
            return True
            
        except Exception as e:
            print(f"[ScanFX] Error applying effects: {e}")
            return False