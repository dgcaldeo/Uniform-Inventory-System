from datetime import date, datetime, time
from flask import Blueprint, render_template
from ..models import Item, Sale, get_setting

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    start = datetime.combine(date.today(), time.min)
    sales = Sale.query.filter(Sale.created_at >= start).all()
    low = Item.query.filter(Item.shelf_qty < int(get_setting("low_stock_threshold"))).all()
    return render_template("dashboard.html", txn_count=len(sales),
                           revenue=sum(s.total for s in sales), low=low)
