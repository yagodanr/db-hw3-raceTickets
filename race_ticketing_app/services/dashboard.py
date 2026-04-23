from ..db import get_connection


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
