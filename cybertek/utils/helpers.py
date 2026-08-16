"""Helper functions and utilities."""
import json


def parse_specs(specs_str):
    """Parse specs string into list."""
    if not specs_str:
        return []
    if isinstance(specs_str, str):
        try:
            return json.loads(specs_str)
        except Exception:
            return [s.strip() for s in specs_str.split(',') if s.strip()]
    return specs_str


def format_specs_for_db(specs_str):
    """Format specs string for database storage."""
    if not specs_str:
        return None
    specs_list = [s.strip() for s in specs_str.split(',') if s.strip()]
    return json.dumps(specs_list) if specs_list else None


def calculate_cart_total(cart_items):
    """Calculate total price for cart items."""
    return sum(item['price'] * item['quantity'] for item in cart_items)
