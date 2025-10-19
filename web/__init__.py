"""Initialize Flask Application."""
from flask import Flask, session

from web.filters import format_cell
from kanaconv  import KanaConv # for pronunciations

conv = KanaConv()

def create_app():
    """Construct the core application."""
    app = Flask(__name__, template_folder="templates")
    app.secret_key = "namae"

    app.template_filter('format_cell')(format_cell)
    # Add the custom filter
    @app.template_filter('hira2roma')
    def hira2roma(text):
        if text=='いっ':
            return "i'"
        else:
            return conv.to_romaji(text)

    with app.app_context():
        from . import routes

        return app

