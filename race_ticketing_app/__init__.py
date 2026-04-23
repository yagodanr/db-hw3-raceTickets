from flask import Flask

from .config import configure_app
from .routes.forms import register_form_routes
from .routes.home import register_home_routes
from .routes.reports import register_report_routes
from .routes.tables import register_table_routes


def create_app():
    app = Flask(__name__, template_folder="../templates")
    configure_app(app)
    register_home_routes(app)
    register_form_routes(app)
    register_report_routes(app)
    register_table_routes(app)
    return app
