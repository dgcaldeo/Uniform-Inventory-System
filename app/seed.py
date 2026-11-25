from datetime import datetime, timedelta
import click
from . import db
from .models import Item, Section, set_setting
from .services import create_sale

SECTIONS = {  # name: (price, [(size, stockroom, shelf)])
    "Boys Polo": (350, [("S", 40, 15), ("M", 35, 4), ("L", 28, 10), ("XL", 12, 5)]),
    "Girls Blouse": (340, [("S", 30, 12), ("M", 30, 10), ("L", 25, 8), ("XL", 10, 4)]),
    "PE Shirt": (280, [("S", 30, 10), ("M", 30, 10), ("L", 25, 8), ("XL", 10, 5)]),
    "Pants / Skirt": (420, [("S", 25, 8), ("M", 25, 8), ("L", 20, 6), ("XL", 10, 4)]),
}
DEMO_SALES = [("Ana Reyes", "M", 2, 1), ("Ben Cruz", "M", 1, 2), ("Cara Lim", "S", 1, 2),
              ("Dan Uy", "M", 3, 3), ("Eli Tan", "L", 1, 5), ("Fay Go", "M", 2, 0)]  # name, size, qty, days ago


def register_cli(app):
    @app.cli.command("init-db")
    @click.option("--reset", is_flag=True, help="Drop all tables first.")
    def init_db(reset):
        """Create tables and load starter data (flask --app run init-db)."""
        if reset:
            db.drop_all()
        db.create_all()
        if Section.query.count():
            click.echo("Tables ready. Data already exists, so nothing was seeded.")
            return
        for name, (price, sizes) in SECTIONS.items():
            sec = Section(name=name, capacity=50)
            for size, stock, shelf in sizes:
                sec.items.append(Item(size=size, price=price, stockroom_qty=stock, shelf_qty=shelf))
            db.session.add(sec)
        set_setting("tax_rate", 12)
        set_setting("low_stock_threshold", 8)
        db.session.commit()
        polo = {i.size: i for i in Section.query.filter_by(name="Boys Polo").one().items}
        for student, size, qty, days in DEMO_SALES:
            polo[size].shelf_qty += qty  # keep demo shelf numbers unchanged after the sale
            create_sale(student, {str(polo[size].id): qty}, datetime.now() - timedelta(days=days))
        click.echo("Database ready with starter data.")
