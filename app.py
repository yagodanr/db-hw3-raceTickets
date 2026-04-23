import os

import pymysql
from flask import Flask, abort, jsonify, render_template

app = Flask(__name__)

TABLE_VIEWS = {
    "brands": {
        "title": "Brands",
        "description": "Organizer brands participating in motorsport events.",
        "query": """
            SELECT
                Name,
                Logo
            FROM Brand
            ORDER BY Name
        """,
    },
    "events": {
        "title": "Race Events",
        "description": "Race events stored in the core schedule.",
        "query": """
            SELECT
                EventID,
                Name,
                Description,
                Date,
                Location
            FROM RaceEvent
            ORDER BY Date, EventID
        """,
    },
    "brand-race-events": {
        "title": "Brand to Race Event Links",
        "description": "Junction table connecting brands with the events they organize or sponsor.",
        "query": """
            SELECT
                bre.BrandName,
                bre.EventID,
                re.Name AS EventName,
                re.Date AS EventDate
            FROM Brand_RaceEvent bre
            JOIN RaceEvent re
              ON re.EventID = bre.EventID
            ORDER BY bre.BrandName, bre.EventID
        """,
    },
    "visitors": {
        "title": "Visitors",
        "description": "Ticket owners and potential buyers.",
        "query": """
            SELECT
                passportID,
                Name,
                Email,
                Phone
            FROM Visitor
            ORDER BY Name, passportID
        """,
    },
    "staff": {
        "title": "Ticketing Staff",
        "description": "Staff members responsible for payment registration and ticket processing.",
        "query": """
            SELECT
                passportID,
                Name
            FROM TicketingStaff
            ORDER BY Name, passportID
        """,
    },
    "payments": {
        "title": "Payments",
        "description": "Payment confirmations tied to visitors and staff members.",
        "query": """
            SELECT
                p.PaymentID,
                p.Status,
                p.Amount,
                p.ConfirmationDate,
                p.VisitorPassportID,
                v.Name AS VisitorName,
                p.StaffPassportID,
                ts.Name AS StaffName
            FROM Payment p
            JOIN Visitor v
              ON v.passportID = p.VisitorPassportID
            JOIN TicketingStaff ts
              ON ts.passportID = p.StaffPassportID
            ORDER BY p.PaymentID
        """,
    },
    "tickets": {
        "title": "Race Tickets",
        "description": "Issued race tickets with ownership, event, and payment linkage.",
        "query": """
            SELECT
                rt.TicketID,
                rt.EventID,
                re.Name AS EventName,
                rt.Price,
                rt.RegisteredAt,
                rt.UsedAt,
                rt.Status,
                rt.OwnerPassportID,
                v.Name AS OwnerName,
                rt.PaymentID,
                rt.RegisteredByStaffPassportID,
                ts.Name AS StaffName
            FROM RaceTicket rt
            JOIN RaceEvent re
              ON re.EventID = rt.EventID
            JOIN Visitor v
              ON v.passportID = rt.OwnerPassportID
            JOIN TicketingStaff ts
              ON ts.passportID = rt.RegisteredByStaffPassportID
            ORDER BY rt.EventID, rt.TicketID
        """,
    },
}


def get_db_config():
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "RaceTicketingDB"),
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
    }


def get_connection():
    return pymysql.connect(**get_db_config())


def fetch_dashboard_data():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DATABASE() AS db_name, VERSION() AS mysql_version")
            metadata = cursor.fetchone()

            counts = {}
            table_queries = {
                "brands": "SELECT COUNT(*) AS total FROM Brand",
                "events": "SELECT COUNT(*) AS total FROM RaceEvent",
                "visitors": "SELECT COUNT(*) AS total FROM Visitor",
                "staff": "SELECT COUNT(*) AS total FROM TicketingStaff",
                "payments": "SELECT COUNT(*) AS total FROM Payment",
                "tickets": "SELECT COUNT(*) AS total FROM RaceTicket",
            }
            for key, query in table_queries.items():
                cursor.execute(query)
                counts[key] = cursor.fetchone()["total"]

            cursor.execute(
                """
                SELECT
                    re.EventID,
                    re.Name,
                    re.Date,
                    re.Location,
                    COUNT(rt.TicketID) AS ticket_count
                FROM RaceEvent re
                LEFT JOIN RaceTicket rt
                  ON rt.EventID = re.EventID
                GROUP BY re.EventID, re.Name, re.Date, re.Location
                ORDER BY re.Date ASC, re.EventID ASC
                LIMIT 5
                """
            )
            upcoming_events = cursor.fetchall()
    finally:
        conn.close()

    return {
        "metadata": metadata,
        "counts": counts,
        "upcoming_events": upcoming_events,
    }


def fetch_table_rows(view_name):
    table_view = TABLE_VIEWS.get(view_name)
    if table_view is None:
        abort(404)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(table_view["query"])
            rows = cursor.fetchall()
    finally:
        conn.close()

    columns = list(rows[0].keys()) if rows else []
    return table_view, columns, rows


@app.route("/")
def home():
    dashboard = None
    db_error = None

    try:
        dashboard = fetch_dashboard_data()
    except pymysql.MySQLError as exc:
        db_error = str(exc)

    return render_template("home.html", dashboard=dashboard, db_error=db_error)


@app.route("/tables/<view_name>")
def table_view(view_name):
    table_config, columns, rows = fetch_table_rows(view_name)
    return render_template(
        "table_view.html",
        table_view=table_config,
        view_name=view_name,
        columns=columns,
        rows=rows,
        table_views=TABLE_VIEWS,
    )


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


if __name__ == "__main__":
    app.run(
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "1") == "1",
    )
