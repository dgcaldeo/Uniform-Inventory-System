from datetime import datetime, timedelta
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func
from .. import db
from ..algorithms.allocation import dp_allocate, equal_split_allocate, greedy_allocate, total_value
from ..models import Sale, SaleItem, Section

bp = Blueprint("planogram", __name__, url_prefix="/planogram")


def _items_for(section):
    """Value = units sold in the last 30 days + 1. Limits come from shelf + stockroom stock."""
    since = datetime.now() - timedelta(days=30)
    sold = dict(db.session.query(SaleItem.item_id, func.sum(SaleItem.qty)).join(Sale)
                .filter(Sale.created_at >= since).group_by(SaleItem.item_id).all())
    out = []
    for it in section.items:
        mx = min(it.max_qty, it.shelf_qty + it.stockroom_qty)
        out.append({"id": it.id, "weight": 1, "value": int(sold.get(it.id, 0)) + 1,
                    "min": min(it.min_qty, mx), "max": mx})
    return out


@bp.route("/")
def index():
    sections = Section.query.order_by(Section.id).all()
    section = db.session.get(Section, request.args.get("section", type=int) or (sections[0].id if sections else 0))
    plan = session.get("plan")
    if not section or not plan or plan["section"] != section.id:
        plan = None
    return render_template("planogram.html", sections=sections, section=section, plan=plan)


@bp.route("/generate", methods=["POST"])
def generate():
    section = db.session.get(Section, request.form.get("section_id", type=int))
    items = _items_for(section)
    try:
        dp = dp_allocate(items, section.capacity)
    except ValueError as err:
        flash(str(err), "error")
        return redirect(url_for("planogram.index", section=section.id))
    session["plan"] = {"section": section.id, "target": {str(k): v for k, v in dp.items()},
                       "totals": {"dp": total_value(items, dp),
                                  "greedy": total_value(items, greedy_allocate(items, section.capacity)),
                                  "equal": total_value(items, equal_split_allocate(items, section.capacity))}}
    return redirect(url_for("planogram.index", section=section.id))


@bp.route("/confirm", methods=["POST"])
def confirm():
    plan = session.pop("plan", None)
    section = db.session.get(Section, request.form.get("section_id", type=int))
    if not plan or not section or plan["section"] != section.id:
        flash("Generate a planogram first.", "error")
        return redirect(url_for("planogram.index"))
    free = section.capacity - section.shelf_total
    for it in section.items:
        move = max(0, plan["target"].get(str(it.id), it.shelf_qty) - it.shelf_qty)
        move = min(move, it.stockroom_qty, free)  # never exceed stockroom stock or shelf capacity
        it.shelf_qty += move
        it.stockroom_qty -= move
        free -= move
    db.session.commit()
    flash("Restock confirmed. Stockroom and shelf updated.", "success")
    return redirect(url_for("planogram.index", section=section.id))


@bp.route("/capacity", methods=["POST"])
def capacity():
    section = db.session.get(Section, request.form.get("section_id", type=int))
    cap = request.form.get("capacity", type=int)
    if not section or not cap or cap < 1:
        flash("Enter a capacity of at least 1 piece.", "error")
    else:
        section.capacity = cap
        session.pop("plan", None)  # old plan was built for the old capacity
        db.session.commit()
        if section.shelf_total > cap:
            flash(f"Capacity saved, but the shelf holds {section.shelf_total} pcs, above {cap}.", "warning")
        else:
            flash(f"{section.name} capacity set to {cap} pcs.", "success")
    return redirect(url_for("planogram.index", section=section.id))
