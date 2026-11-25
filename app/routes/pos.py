from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from .. import db
from ..models import Item, Sale, Section
from ..services import build_cart, create_sale

bp = Blueprint("pos", __name__)


@bp.route("/pos")
def index():
    cart = session.get("cart", {})
    return render_template("pos.html", sections=Section.query.order_by(Section.id).all(),
                           cart=build_cart(cart), in_cart=cart)


@bp.route("/pos/add/<int:item_id>", methods=["POST"])
def add(item_id):
    item, cart = db.session.get(Item, item_id), session.get("cart", {})
    if item and cart.get(str(item_id), 0) < item.shelf_qty:
        cart[str(item_id)] = cart.get(str(item_id), 0) + 1
        session["cart"] = cart
    return redirect(url_for("pos.index"))


@bp.route("/pos/remove/<int:item_id>", methods=["POST"])
def remove(item_id):
    cart = session.get("cart", {})
    if cart.get(str(item_id), 0) > 1:
        cart[str(item_id)] -= 1
    else:
        cart.pop(str(item_id), None)
    session["cart"] = cart
    return redirect(url_for("pos.index"))


@bp.route("/pos/checkout", methods=["POST"])
def checkout():
    student = request.form.get("student_name", "").strip()
    if not student:
        flash("Enter the student's name.", "error")
        return redirect(url_for("pos.index"))
    try:
        sale = create_sale(student, session.get("cart", {}))
    except ValueError as err:
        flash(str(err), "error")
        return redirect(url_for("pos.index"))
    session["cart"] = {}
    return redirect(url_for("pos.receipt", sale_id=sale.id))


@bp.route("/receipt/<int:sale_id>")
def receipt(sale_id):
    return render_template("receipt.html", sale=Sale.query.get_or_404(sale_id))
