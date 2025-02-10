import sys, os

sys.path.insert(1, os.path.dirname(__file__))

from web import create_app
application = create_app()