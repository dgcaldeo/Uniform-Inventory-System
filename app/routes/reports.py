import io
from datetime import date, datetime, time, timedelta
from flask import Blueprint, render_template, request, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from .. import db
from ..models import Sale, SaleItem

bp = Blueprint("reports", __name__, url_prefix="/reports")


def _range(period, date_str):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        d = date.today()
    if period == "weekly":
        start = d - timedelta(days=d.weekday())  # Monday
        end = start + timedelta(days=7)
        label = f"Weekly report: {start:%b %d, %Y} to {(end - timedelta(days=1)):%b %d, %Y}"
    else:
        period, start, end = "daily", d, d + timedelta(days=1)
        label = f"Daily report: {d:%B %d, %Y}"
    return period, d, datetime.combine(start, time.min), datetime.combine(end, time.min), label


def _data():
    period, d, start, end, label = _range(request.args.get("period"), request.args.get("date"))
    rows = (db.session.query(Sale, SaleItem).join(SaleItem, SaleItem.sale_id == Sale.id)
            .filter(Sale.created_at >= start, Sale.created_at < end).order_by(Sale.created_at).all())
    return {"period": period, "date": d, "label": label, "rows": rows,
            "txns": len({s.id for s, _ in rows}),
            "total_tax": sum(i.tax_amount for _, i in rows), "total_amount": sum(i.line_total for _, i in rows)}


@bp.route("/")
def index():
    return render_template("reports.html", **_data())


@bp.route("/pdf")
def pdf():
    d = _data()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), title=d["label"])
    styles = getSampleStyleSheet()
    table_rows = [["Date / Time", "Student", "Item", "Qty", "Unit Price", "Tax", "Total"]]
    for sale, it in d["rows"]:
        table_rows.append([f"{sale.created_at:%Y-%m-%d %H:%M}", sale.student_name, it.item_name, it.qty,
                           f"PHP {it.unit_price:,.2f}", f"PHP {it.tax_amount:,.2f}", f"PHP {it.line_total:,.2f}"])
    table_rows.append(["", "", "", "", "TOTAL", f"PHP {d['total_tax']:,.2f}", f"PHP {d['total_amount']:,.2f}"])
    table = Table(table_rows, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("ALIGN", (3, 1), (-1, -1), "RIGHT")]))
    doc.build([Paragraph("Uniform Shop Sales Report", styles["Title"]), Paragraph(d["label"], styles["Normal"]),
               Spacer(1, 12), table])
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf", as_attachment=True,
                     download_name=f"sales-report-{d['period']}-{d['date']}.pdf")
