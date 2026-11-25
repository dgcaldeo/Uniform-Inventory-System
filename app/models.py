from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from . import db


def money(x):
    return Decimal(x).quantize(Decimal("0.01"), ROUND_HALF_UP)


DEFAULTS = {"tax_rate": "12", "low_stock_threshold": "8"}


class Setting(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(100), nullable=False)


def get_setting(key):
    row = db.session.get(Setting, key)
    return row.value if row else DEFAULTS[key]


def set_setting(key, value):
    row = db.session.get(Setting, key)
    if row:
        row.value = str(value)
    else:
        db.session.add(Setting(key=key, value=str(value)))


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=50)  # max pcs on shelf
    items = db.relationship("Item", back_populates="section", order_by="Item.id")

    @property
    def shelf_total(self):
        return sum(i.shelf_qty for i in self.items)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey("section.id"), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    min_qty = db.Column(db.Integer, nullable=False, default=5)   # min pcs kept on shelf
    max_qty = db.Column(db.Integer, nullable=False, default=25)  # max pcs on shelf
    stockroom_qty = db.Column(db.Integer, nullable=False, default=0)
    shelf_qty = db.Column(db.Integer, nullable=False, default=0)
    section = db.relationship("Section", back_populates="items")

    @property
    def name(self):
        return f"{self.section.name} — {self.size}"

    @property
    def low(self):
        return self.shelf_qty < int(get_setting("low_stock_threshold"))


class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    item = db.relationship("Item")


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False)
    tax_total = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    items = db.relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sale.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=True)
    item_name = db.Column(db.String(100), nullable=False)  # snapshot, survives renames
    qty = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(10, 2), nullable=False)  # qty x price + tax
    sale = db.relationship("Sale", back_populates="items")
