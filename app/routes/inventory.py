from decimal import Decimal, InvalidOperation
from flask import Blueprint, flash, redirect, render_template, request, url_for
from .. import db
from ..models import Delivery, Item, Section, get_setting, set_setting

bp = Blueprint("inventory", __name__)


def _dec(value):
    try:
        d = Decimal(value)
        return d if d >= 0 else None
    except (InvalidOperation, TypeError):
        return None


@bp.route("/stockroom")
def stockroom():
    return render_template("stockroom.html", sections=Section.query.order_by(Section.id).all(),
                           items=Item.query.order_by(Item.id).all(),
                           deliveries=Delivery.query.order_by(Delivery.id.desc()).limit(8).all())


@bp.route("/stockroom/delivery", methods=["POST"])
def delivery():
    item = db.session.get(Item, request.form.get("item_id", type=int))
    qty = request.form.get("qty", type=int)
    if not item or not qty or qty <= 0:
        flash("Choose an item and enter a quantity above 0.", "error")
    else:
        item.stockroom_qty += qty
        db.session.add(Delivery(item_id=item.id, qty=qty))
        db.session.commit()
        flash(f"Added {qty} pcs of {item.name} to the stockroom.", "success")
    return redirect(url_for("inventory.stockroom"))


@bp.route("/items")
def items():
    return render_template("items.html", sections=Section.query.order_by(Section.id).all(),
                           tax_rate=get_setting("tax_rate"), threshold=get_setting("low_stock_threshold"))


@bp.route("/items/add", methods=["POST"])
def add_item():
    f = request.form
    new_name = f.get("new_section", "").strip()
    price, size = _dec(f.get("price")), f.get("size", "").strip()
    if new_name:
        section = Section.query.filter_by(name=new_name).first() or Section(
            name=new_name, capacity=f.get("capacity", 50, type=int))
        db.session.add(section)
    else:
        section = db.session.get(Section, f.get("section_id", type=int))
    if not section or not size or price is None:
        flash("Pick a section, enter a size and a valid price.", "error")
        return redirect(url_for("inventory.items"))
    if any(i.size.lower() == size.lower() for i in section.items):
        flash(f"{section.name} already has size {size}.", "error")
        return redirect(url_for("inventory.items"))
    db.session.add(Item(section=section, size=size, price=price,
                        min_qty=f.get("min_qty", 5, type=int), max_qty=f.get("max_qty", 25, type=int),
                        stockroom_qty=f.get("stockroom_qty", 0, type=int)))
    db.session.commit()
    flash(f"Added {section.name} — {size}.", "success")
    return redirect(url_for("inventory.items"))


@bp.route("/items/<int:item_id>/edit", methods=["POST"])
def edit_item(item_id):
    item = db.session.get(Item, item_id)
    price = _dec(request.form.get("price"))
    mn, mx = request.form.get("min_qty", type=int), request.form.get("max_qty", type=int)
    if not item or price is None or mn is None or mx is None or mn < 0 or mx < mn:
        flash("Enter a valid price and a max that is at least the min.", "error")
    else:
        item.price, item.min_qty, item.max_qty = price, mn, mx
        db.session.commit()
        flash(f"Updated {item.name}. New prices apply to future sales only.", "success")
    return redirect(url_for("inventory.items"))


@bp.route("/settings", methods=["POST"])
def settings():
    tax, threshold = _dec(request.form.get("tax_rate")), request.form.get("threshold", type=int)
    if tax is None or tax > 100 or threshold is None or threshold < 0:
        flash("Tax must be 0–100 and the threshold 0 or more.", "error")
    else:
        set_setting("tax_rate", tax)
        set_setting("low_stock_threshold", threshold)
        db.session.commit()
        flash("Settings saved.", "success")
    return redirect(url_for("inventory.items"))
