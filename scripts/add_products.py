from django.apps import apps
from decimal import Decimal
import random

# --- helpers to locate models by class name (no need to know app label) ---
def get_model(name):
    for m in apps.get_models():
        if m.__name__ == name:
            return m
    raise LookupError(f"Model {name} not found; check your app/model names.")

Shop = get_model("Shop")
Category = get_model("Category")
Product = get_model("Product")

# --- get the target shop ---
shop = Shop.objects.get(id=1, slug="master")
print(f"Seeding products for shop: {shop}")

# --- create/reuse categories for this shop ---
category_names = [
    "Pens", "Pencils", "Markers", "Notebooks", "Paper",
    "Art Supplies", "Rulers & Geometry", "Adhesives", "Files & Folders", "Misc"
]
categories = []
for name in category_names:
    cat, _ = Category.objects.get_or_create(shop=shop, name=name)
    categories.append(cat)
print(f"Categories ready: {[c.name for c in categories]}")

# --- EAN-13 check digit calc ---
def ean13_check_digit(base12: str) -> str:
    # base12: 12-digit numeric string
    assert len(base12) == 12 and base12.isdigit()
    odd_sum = sum(int(d) for i, d in enumerate(base12) if i % 2 == 0)      # positions 1,3,5,...
    even_sum = sum(int(d) for i, d in enumerate(base12) if i % 2 == 1)     # positions 2,4,6,...
    total = odd_sum + 3 * even_sum
    return str((10 - (total % 10)) % 10)

def new_barcode(prefix="200"):  # '2' ranges are often used for internal codes
    # creates a unique barcode for this shop
    assert prefix.isdigit() and len(prefix) < 12
    while True:
        rest_len = 12 - len(prefix)
        base12 = prefix + "".join(random.choices("0123456789", k=rest_len))
        code = base12 + ean13_check_digit(base12)
        if not Product.objects.filter(shop=shop, barcode=code).exists():
            return code

# --- name parts for a bit of variety (unique name not required, barcode is the unique constraint) ---
colors = ["Blue", "Black", "Red", "Green", "Purple", "Orange", "Yellow", "Pink", "Cyan", "Gray"]
items = [
    "Ballpoint Pen", "Gel Pen", "HB Pencil", "Mechanical Pencil", "Highlighter",
    "A4 Notebook", "Spiral Notebook", "Drawing Pad", "Sticky Notes", "Marker",
    "Ruler 30cm", "Eraser", "Glue Stick", "Correction Pen", "Folder",
    "Paper Ream A4", "Index Tabs", "Stapler", "Staples", "Binder"
]

def run():
    # --- create 50 products ---
    created = 0
    for i in range(50):
        category = random.choice(categories)
        name = f"{random.choice(colors)} {random.choice(items)}"
        price = Decimal(f"{random.randint(5, 500)}.{random.randint(0,99):02d}")
        discount = Decimal(random.choice([0, 5, 10, 15, 20]))
        stock = random.randint(0, 200)
        barcode = new_barcode(prefix="200")

        p = Product(
            shop=shop,
            name=name,
            barcode=barcode,
            price=price,
            stock_quantity=stock,
            discount_percentage=discount,
            category=category,  # if you omit this, your save() will assign 'Uncategorized'
        )
        p.save()  # triggers full_clean and computes price_after_discount
        created += 1
        print(f"#{created:02d} {p.name} | {category.name} | {p.barcode} | {p.price} | stock {p.stock_quantity}")

    print(f"\n✅ Done. Created {created} products for shop '{shop.slug}'.")
