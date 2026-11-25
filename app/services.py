from datetime import datetime
from decimal import Decimal
from . import db
from .models import Item, Sale, SaleItem, get_setting, money


def build_cart(cart):
    """cart = {item_id(str): qty}. Returns lines plus subtotal / tax / total."""
    rate = Decimal(get_setting("tax_rate"))
    lines, subtotal, tax = [], Decimal(0), Decimal(0)
    for item_id, qty in cart.items():
        item = db.session.get(Item, int(item_id))
        if not item or qty <= 0:
            continue
        sub = money(item.price * qty)
        line_tax = money(sub * rate / 100)
        lines.append({"item": item, "qty": qty, "subtotal": sub, "tax": line_tax, "total": sub + line_tax})
        subtotal += sub
        tax += line_tax
    return {"lines": lines, "subtotal": subtotal, "tax": tax, "total": subtotal + tax, "rate": rate}


def create_sale(student, cart, when=None):
    data = build_cart(cart)
    if not data["lines"]:
        raise ValueError("The cart is empty.")
    for line in data["lines"]:
        if line["qty"] > line["item"].shelf_qty:
            raise ValueError(f"Only {line['item'].shelf_qty} pcs of {line['item'].name} on the shelf.")
    sale = Sale(student_name=student, created_at=when or datetime.now(), subtotal=data["subtotal"],
                tax_rate=data["rate"], tax_total=data["tax"], total=data["total"])
    for line in data["lines"]:
        item = line["item"]
        sale.items.append(SaleItem(item_id=item.id, item_name=item.name, qty=line["qty"],
                                   unit_price=item.price, tax_amount=line["tax"], line_total=line["total"]))
        item.shelf_qty -= line["qty"]  # sale deducts from the shelf, not the stockroom
    db.session.add(sale)
    db.session.commit()
    return sale
