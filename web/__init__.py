"""Initialize Flask Application."""
import os
from flask import Flask, session

from web.filters import format_cell, multisort_filter
from kanaconv  import KanaConv # for pronunciations

conv = KanaConv()

def create_app():
    """Construct the core application."""
    app = Flask(__name__, template_folder="templates")
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())

    app.template_filter('format_cell')(format_cell)
    app.template_filter('multisort')(multisort_filter)
    # Add the custom filter
    @app.template_filter('hira2roma')
    def hira2roma(text):
        if text=='いっ':
            return "i'"
        else:
            return conv.to_romaji(text)

    with app.app_context():
        from . import routes
        from .db import close_db
        app.teardown_appcontext(close_db)

        return app

