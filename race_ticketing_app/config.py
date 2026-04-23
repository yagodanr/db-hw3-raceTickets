import os


def configure_app(app):
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "race-ticketing-dev-secret")
