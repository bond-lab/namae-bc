"""Initialize Flask Application."""
from flask import Flask, session

from web.filters import format_cell

def create_app():
    """Construct the core application."""
    app = Flask(__name__, template_folder="templates")
    app.secret_key = "namae"

    app.template_filter('format_cell')(format_cell)

    with app.app_context():
        from . import routes

        return app

