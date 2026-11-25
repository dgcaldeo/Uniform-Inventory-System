# Uniform Shop: Planogram + POS (Flask)

Shelf allocation (bounded knapsack DP) with stockroom, POS, receipts, tax, and daily/weekly reports.

## Setup
```bash
python -m venv venv
venv\Scripts\activate        # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env       # macOS/Linux: cp .env.example .env
```
**MySQL:** create the database, then put your password in `.env` (`DATABASE_URL`).
```sql
CREATE DATABASE uniform_shop CHARACTER SET utf8mb4;
```
If `DATABASE_URL` is unset, the app uses a local SQLite file so you can try it right away.

```bash
flask --app run init-db      # create tables + starter data (add --reset to wipe and reseed)
flask --app run run          # or: python run.py  → http://127.0.0.1:5000
```

## Structure
```
run.py  config.py  requirements.txt  .env.example
app/
  __init__.py        app factory
  models.py          Section, Item, Delivery, Sale, SaleItem, Setting
  services.py        cart totals + create_sale (tax, shelf deduction)
  seed.py            `init-db` command and starter data
  algorithms/allocation.py   dp_allocate, greedy_allocate, equal_split_allocate (pure Python, unit-testable)
  routes/            dashboard, inventory (stockroom, items, settings), planogram, pos (+receipt), reports (+PDF)
  templates/  static/css/
```

## Notes
- Tax is added on top of the item price (default 12%, editable on Items & Pricing). Confirm the rate with your client.
- Planogram value score = units sold in the last 30 days + 1. Change `_items_for()` in `routes/planogram.py` to add margin or other factors.
- Section capacity is editable on the Planogram tab. Lowering it below the current shelf count shows a warning.
- PDF export uses ReportLab, so amounts print as "PHP" (its default font has no ₱ glyph).
