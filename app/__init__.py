from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    app.jinja_env.filters["peso"] = lambda v: f"₱{(v or 0):,.2f}"

    from .routes import dashboard, inventory, planogram, pos, reports
    for module in (dashboard, inventory, planogram, pos, reports):
        app.register_blueprint(module.bp)

    from .seed import register_cli
    register_cli(app)
    return app
