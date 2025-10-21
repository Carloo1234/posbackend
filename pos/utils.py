CATEGORY_COLORS_MAPPING = {
    "gray": "#9e9e9e",
    "red": "#ef4444",
    "blue": "#3b82f6",
    "green": "#22c55e",
    "yellow": "#eab308",
    "brown": "#92400e",
    "orange": "#f97316",
}

# For models.py
CATEGORY_COLORS_CHOICES = [(color, color.capitalize()) for color in CATEGORY_COLORS_MAPPING.keys()]




def generate_ean13_without_check(data: str):
    if not len(data) == 12 or not data.isdigit():
        return -1
        
    digits = [int(d) for d in data]
    total = sum(d if i % 2 == 0 else d * 3 for i, d in enumerate(digits))
    check_digit = (10 - (total % 10)) % 10
    return data + str(check_digit)

def is_valid_ean13(barcode):
    barcode_without_check = barcode[:-1]
    correct_barcode = generate_ean13_without_check(barcode_without_check)
    return correct_barcode == barcode