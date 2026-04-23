import os

import pymysql
from flask import Flask, jsonify, render_template

app = Flask(__name__)


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


@app.route("/")
def home():
    dashboard = None
    db_error = None

    try:
        dashboard = fetch_dashboard_data()
    except pymysql.MySQLError as exc:
        db_error = str(exc)

    return render_template("home.html", dashboard=dashboard, db_error=db_error)


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
        }
    )


if __name__ == "__main__":
    app.run(
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "1") == "1",
    )
