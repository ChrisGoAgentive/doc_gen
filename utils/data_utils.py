import json
import os
from datetime import datetime

class DataLoader:
    """
    Handles robust loading and querying of JSON data sources.
    """
    
    @staticmethod
    def load(filepath):
        """
        Safely loads JSON data from a file.
        Always returns a list, even if the source is a single object.
        """
        if not os.path.exists(filepath):
            print(f"[DataLoader] Error: File '{filepath}' not found.")
            return []
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Normalize to list to ensure consistent iteration
            if isinstance(data, dict):
                return [data]
            elif isinstance(data, list):
                return data
            else:
                print(f"[DataLoader] Warning: JSON root in '{filepath}' is not a list or dict.")
                return []
                
        except json.JSONDecodeError as e:
            print(f"[DataLoader] Error decoding JSON in '{filepath}': {e}")
            return []
        except Exception as e:
            print(f"[DataLoader] Unexpected error loading '{filepath}': {e}")
            return []

    @staticmethod
    def find_record(data_list, key, value):
        """
        Finds the first record in a list where record[key] == value.
        Useful for finding specific IDs.
        """
        if not data_list:
            return None
            
        for item in data_list:
            if isinstance(item, dict) and item.get(key) == value:
                return item
        return None

class DataFormatter:
    """
    Static methods to format raw data for presentation.
    These are designed to be used as Jinja2 filters.
    """

    @staticmethod
    def format_currency(value, symbol="$"):
        """
        Formats a number as currency (e.g., 1234.5 -> $1,234.50).
        Handles string inputs gracefully.
        """
        if value is None:
            return ""
        try:
            # Clean string inputs like "$1000" -> 1000.0
            if isinstance(value, str):
                clean_val = value.replace('$', '').replace(',', '')
                val_float = float(clean_val)
            else:
                val_float = float(value)
            
            return "{}{:,.2f}".format(symbol, val_float)
        except (ValueError, TypeError):
            # If conversion fails, return original value
            return value

    @staticmethod
    def format_date(value, input_fmt="%Y-%m-%d", output_fmt="%B %d, %Y"):
        """
        Formats a date string (e.g., "2024-12-01" -> "December 01, 2024").
        """
        if not value:
            return ""
        try:
            if isinstance(value, datetime):
                dt = value
            else:
                # Basic ISO handling if needed, or custom format
                dt = datetime.strptime(str(value), input_fmt)
            return dt.strftime(output_fmt)
        except (ValueError, TypeError):
            return value
    
    @staticmethod
    def format_phone(value):
        """
        Formats a 10-digit number into US phone format: (555) 123-4567.
        """
        if not value:
            return ""
        
        # Remove non-digits
        clean = ''.join(filter(str.isdigit, str(value)))
        
        if len(clean) == 10:
            return f"({clean[:3]}) {clean[3:6]}-{clean[6:]}"
        return value
    
    @staticmethod
    def format_digits_only(value):
        """
        Removes all non-digit characters from a string.
        Useful for cleaning SSNs (removing dashes) or Account Numbers.
        Example: "123-45-6789" -> "123456789"
        """
        if not value:
            return ""
        return ''.join(filter(str.isdigit, str(value)))