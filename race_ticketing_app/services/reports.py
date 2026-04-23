from datetime import datetime
from decimal import Decimal

from ..db import get_connection


def serialize_value(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return value


def serialize_rows(rows):
    return [{key: serialize_value(value) for key, value in row.items()} for row in rows]


REPORT_DEFINITIONS = {
    "payment-confirmations": {
        "title": "Report 1: Payment Confirmation Document",
        "document_name": "Document A: Payment Confirmation",
        "description": (
            "Prints one selected payment confirmation together with the responsible visitor and "
            "staff member. The report is parameterized by PaymentID so the output corresponds "
            "to one concrete output document rather than the whole register."
        ),
        "queries": [
            {
                "title": "Query 1. Print the selected payment confirmation document",
                "sql": """
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
WHERE p.PaymentID = %s;
                """.strip(),
            },
            {
                "title": "Query 2. Print tickets linked to the selected payment",
                "sql": """
SELECT
    rt.TicketID,
    rt.EventID,
    re.Name AS EventName,
    re.Date AS EventDate,
    v.Name AS VisitorName,
    rt.Price,
    rt.RegisteredAt,
    rt.Status,
    ts.Name AS StaffName
FROM RaceTicket rt
JOIN RaceEvent re
  ON re.EventID = rt.EventID
JOIN Visitor v
  ON v.passportID = rt.OwnerPassportID
JOIN TicketingStaff ts
  ON ts.passportID = rt.RegisteredByStaffPassportID
WHERE rt.PaymentID = %s
ORDER BY rt.EventID, rt.TicketID;
                """.strip(),
            },
        ],
        "runner": "_fetch_payment_confirmation_report",
    },
    "printed-tickets": {
        "title": "Report 2: Printed Ticket Document",
        "document_name": "Document B: Ticket / Printed Ticket",
        "description": (
            "Prints one selected ticket together with its event, owner, payment, and registration "
            "information. The report is parameterized by the selected ticket key so the output "
            "corresponds to one concrete printed ticket document."
        ),
        "queries": [
            {
                "title": "Query 1. Print the selected ticket document",
                "sql": """
SELECT
    rt.TicketID,
    rt.EventID,
    re.Name AS EventName,
    re.Date AS EventDate,
    re.Location,
    v.Name AS VisitorName,
    rt.Price,
    rt.RegisteredAt AS IssueDate,
    rt.Status,
    p.PaymentID,
    p.Amount AS PaymentAmount,
    ts.Name AS StaffName
FROM RaceTicket rt
JOIN RaceEvent re
  ON rt.EventID = re.EventID
JOIN Visitor v
  ON v.passportID = rt.OwnerPassportID
JOIN Payment p
  ON p.PaymentID = rt.PaymentID
JOIN TicketingStaff ts
  ON ts.passportID = rt.RegisteredByStaffPassportID
WHERE rt.TicketID = %s AND rt.EventID = %s;
                """.strip(),
            },
            {
                "title": "Query 2. Print brands linked to the selected ticket event",
                "sql": """
SELECT
    bre.EventID,
    b.Name AS BrandName,
    b.Logo
FROM Brand_RaceEvent bre
JOIN Brand b
  ON b.Name = bre.BrandName
WHERE bre.EventID = %s
ORDER BY b.Name;
                """.strip(),
            },
        ],
        "runner": "_fetch_printed_ticket_report",
    },
    "ticket-records": {
        "title": "Report 3: Ticket Record Document",
        "document_name": "Document C: Ticket Record",
        "description": (
            "Prints one selected ticket record together with its registration state. The report is "
            "parameterized by the selected ticket key so the output corresponds to one concrete "
            "ticket record document."
        ),
        "queries": [
            {
                "title": "Query 1. Print the selected ticket record document",
                "sql": """
SELECT
    CONCAT(rt.TicketID, '-', rt.EventID) AS RecordID,
    rt.TicketID,
    rt.EventID,
    re.Name AS EventName,
    rt.Status,
    rt.RegisteredAt AS CreatedAt,
    rt.UsedAt,
    rt.PaymentID,
    v.Name AS VisitorName,
    ts.Name AS StaffName
FROM RaceTicket rt
JOIN RaceEvent re
  ON re.EventID = rt.EventID
JOIN Visitor v
  ON v.passportID = rt.OwnerPassportID
JOIN TicketingStaff ts
  ON ts.passportID = rt.RegisteredByStaffPassportID
WHERE rt.TicketID = %s AND rt.EventID = %s;
                """.strip(),
            },
            {
                "title": "Query 2. Print the payment confirmation linked to the selected record",
                "sql": """
SELECT
    p.PaymentID,
    p.Status,
    p.Amount,
    p.ConfirmationDate,
    v.Name AS VisitorName,
    ts.Name AS StaffName
FROM RaceTicket rt
JOIN Payment p
  ON p.PaymentID = rt.PaymentID
JOIN Visitor v
  ON v.passportID = p.VisitorPassportID
JOIN TicketingStaff ts
  ON ts.passportID = p.StaffPassportID
WHERE rt.TicketID = %s AND rt.EventID = %s;
                """.strip(),
            },
        ],
        "runner": "_fetch_ticket_record_report",
    },
}


def _run_report_queries(summary_sql, detail_sql, summary_params=None, detail_params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(summary_sql, summary_params or ())
            summary_rows = serialize_rows(cursor.fetchall())
            cursor.execute(detail_sql, detail_params or ())
            detail_rows = serialize_rows(cursor.fetchall())
    finally:
        conn.close()

    return summary_rows, detail_rows


def fetch_payment_options():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    p.PaymentID AS value,
                    CONCAT(
                        '#', p.PaymentID, ' | ',
                        v.Name, ' | ',
                        p.Status, ' | ',
                        DATE_FORMAT(p.ConfirmationDate, '%Y-%m-%d %H:%i')
                    ) AS label
                FROM Payment p
                JOIN Visitor v
                  ON v.passportID = p.VisitorPassportID
                ORDER BY p.PaymentID DESC
                """
            )
            return cursor.fetchall()
    finally:
        conn.close()


def fetch_ticket_options():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    CONCAT(rt.TicketID, '||', rt.EventID) AS value,
                    CONCAT(
                        rt.TicketID, ' | ',
                        re.Name, ' | event ', rt.EventID, ' | ',
                        v.Name
                    ) AS label
                FROM RaceTicket rt
                JOIN RaceEvent re
                  ON re.EventID = rt.EventID
                JOIN Visitor v
                  ON v.passportID = rt.OwnerPassportID
                ORDER BY rt.EventID, rt.TicketID
                """
            )
            return cursor.fetchall()
    finally:
        conn.close()


def _fetch_default_payment_id():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT PaymentID FROM Payment ORDER BY PaymentID DESC LIMIT 1")
            row = cursor.fetchone()
            return None if row is None else row["PaymentID"]
    finally:
        conn.close()


def _fetch_default_ticket_key():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT TicketID, EventID FROM RaceTicket ORDER BY EventID, TicketID LIMIT 1")
            row = cursor.fetchone()
            return None if row is None else (row["TicketID"], row["EventID"])
    finally:
        conn.close()


def _fetch_payment_confirmation_report(config, payment_id=None):
    selected_payment_id = payment_id if payment_id is not None else _fetch_default_payment_id()
    if selected_payment_id is None:
        return {
            "summary_title": "Selected Payment Confirmation",
            "detail_title": "Tickets Linked to the Selected Payment",
            "summary_rows": [],
            "detail_rows": [],
            "selected_payment_id": None,
            "payment_options": [],
        }

    summary_rows, detail_rows = _run_report_queries(
        config["queries"][0]["sql"],
        config["queries"][1]["sql"],
        (selected_payment_id,),
        (selected_payment_id,),
    )
    return {
        "summary_title": "Selected Payment Confirmation",
        "detail_title": "Tickets Linked to the Selected Payment",
        "summary_rows": summary_rows,
        "detail_rows": detail_rows,
        "selected_payment_id": selected_payment_id,
        "payment_options": fetch_payment_options(),
    }


def _fetch_printed_ticket_report(config, ticket_id=None, event_id=None):
    selected_ticket = (ticket_id, event_id) if ticket_id is not None and event_id is not None else _fetch_default_ticket_key()
    if selected_ticket is None:
        return {
            "summary_title": "Selected Printed Ticket",
            "detail_title": "Brands Linked to the Selected Ticket Event",
            "summary_rows": [],
            "detail_rows": [],
            "selected_ticket_key": None,
            "ticket_options": [],
        }

    summary_rows, detail_rows = _run_report_queries(
        config["queries"][0]["sql"],
        config["queries"][1]["sql"],
        selected_ticket,
        (selected_ticket[1],),
    )
    return {
        "summary_title": "Selected Printed Ticket",
        "detail_title": "Brands Linked to the Selected Ticket Event",
        "summary_rows": summary_rows,
        "detail_rows": detail_rows,
        "selected_ticket_key": f"{selected_ticket[0]}||{selected_ticket[1]}",
        "ticket_options": fetch_ticket_options(),
    }


def _fetch_ticket_record_report(config, ticket_id=None, event_id=None):
    selected_ticket = (ticket_id, event_id) if ticket_id is not None and event_id is not None else _fetch_default_ticket_key()
    if selected_ticket is None:
        return {
            "summary_title": "Selected Ticket Record",
            "detail_title": "Payment Confirmation Linked to the Selected Record",
            "summary_rows": [],
            "detail_rows": [],
            "selected_ticket_key": None,
            "ticket_options": [],
        }

    summary_rows, detail_rows = _run_report_queries(
        config["queries"][0]["sql"],
        config["queries"][1]["sql"],
        selected_ticket,
        selected_ticket,
    )
    return {
        "summary_title": "Selected Ticket Record",
        "detail_title": "Payment Confirmation Linked to the Selected Record",
        "summary_rows": summary_rows,
        "detail_rows": detail_rows,
        "selected_ticket_key": f"{selected_ticket[0]}||{selected_ticket[1]}",
        "ticket_options": fetch_ticket_options(),
    }


def fetch_reports_index():
    payment_options = []
    ticket_options = []
    try:
        payment_options = fetch_payment_options()
    except Exception:
        payment_options = []
    try:
        ticket_options = fetch_ticket_options()
    except Exception:
        ticket_options = []
    return [
        {
            "slug": slug,
            "title": config["title"],
            "document_name": config["document_name"],
            "description": config["description"],
            "payment_options": payment_options if slug == "payment-confirmations" else [],
            "ticket_options": ticket_options if slug in {"printed-tickets", "ticket-records"} else [],
        }
        for slug, config in REPORT_DEFINITIONS.items()
    ]


def fetch_report(report_slug, **params):
    config = REPORT_DEFINITIONS.get(report_slug)
    if config is None:
        from flask import abort

        abort(404)

    runner = globals()[config["runner"]]
    report_data = runner(config, **params)
    return {
        "slug": report_slug,
        "title": config["title"],
        "document_name": config["document_name"],
        "description": config["description"],
        "queries": config["queries"],
        **report_data,
    }


def fetch_report_documentation():
    docs = []
    for slug in REPORT_DEFINITIONS:
        report = fetch_report(slug)
        docs.append(
            {
                "slug": slug,
                "title": report["title"],
                "document_name": report["document_name"],
                "description": report["description"],
                "queries": report["queries"],
                "summary_title": report["summary_title"],
                "summary_rows": report["summary_rows"],
                "detail_title": report["detail_title"],
                "detail_rows": report["detail_rows"],
            }
        )
    return docs
