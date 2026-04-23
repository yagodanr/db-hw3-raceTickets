import pymysql
from flask import jsonify, render_template

from ..metadata import TABLE_VIEWS
from ..services.assignment_docs import fetch_assignment_docs
from ..services.dashboard import fetch_dashboard_data
from ..table_utils import format_value_for_form


def register_home_routes(app):
    @app.route("/")
    def home():
        dashboard = None
        db_error = None

        try:
            dashboard = fetch_dashboard_data()
        except pymysql.MySQLError as exc:
            db_error = str(exc)

        return render_template(
            "home.html",
            dashboard=dashboard,
            db_error=db_error,
            table_views=TABLE_VIEWS,
        )

    @app.route("/forms")
    def forms_home():
        return render_template("forms_home.html")

    @app.route("/forms/documentation")
    def forms_documentation():
        from flask import flash

        try:
            docs = fetch_assignment_docs()
        except pymysql.MySQLError as exc:
            flash(f"Could not build documentation snapshots: {exc}", "error")
            docs = []
        return render_template("forms_documentation.html", docs=docs)

    @app.route("/db-status")
    def db_status():
        try:
            dashboard = fetch_dashboard_data()
        except pymysql.MySQLError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 500

        return jsonify(
            {
                "ok": True,
                "database": dashboard["metadata"]["db_name"],
                "mysql_version": dashboard["metadata"]["mysql_version"],
                "counts": dashboard["counts"],
                "table_views": list(TABLE_VIEWS.keys()),
            }
        )

    @app.context_processor
    def inject_helpers():
        return {"format_value_for_form": format_value_for_form}
