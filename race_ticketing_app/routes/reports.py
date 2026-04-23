import pymysql
from flask import flash, render_template, request

from ..services.reports import fetch_report, fetch_report_documentation, fetch_reports_index


def register_report_routes(app):
    @app.route("/reports")
    def reports_home():
        return render_template("reports_home.html", reports=fetch_reports_index())

    @app.route("/reports/documentation")
    def reports_documentation():
        try:
            docs = fetch_report_documentation()
        except pymysql.MySQLError as exc:
            flash(f"Could not build report documentation snapshots: {exc}", "error")
            docs = []
        return render_template("reports_documentation.html", docs=docs)

    @app.route("/reports/<report_slug>")
    def report_view(report_slug):
        report = None
        db_error = None
        try:
            payment_id = request.args.get("payment_id", "").strip()
            ticket_key = request.args.get("ticket_key", "").strip()
            if report_slug == "payment-confirmations" and payment_id:
                report = fetch_report(report_slug, payment_id=int(payment_id))
            elif report_slug in {"printed-tickets", "ticket-records"} and ticket_key:
                ticket_id, event_id = ticket_key.split("||", 1)
                report = fetch_report(report_slug, ticket_id=ticket_id, event_id=int(event_id))
            else:
                report = fetch_report(report_slug)
        except pymysql.MySQLError as exc:
            db_error = str(exc)
        except ValueError:
            db_error = "The selected report key is invalid."
        return render_template("report_view.html", report=report, db_error=db_error)
