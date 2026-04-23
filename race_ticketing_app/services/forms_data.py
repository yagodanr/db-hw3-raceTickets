from ..db import get_connection


def fetch_payment_form_data():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    passportID AS value,
                    CONCAT(Name, ' | ', passportID) AS label
                FROM Visitor
                ORDER BY Name, passportID
                """
            )
            visitors = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    passportID AS value,
                    CONCAT(Name, ' | ', passportID) AS label
                FROM TicketingStaff
                ORDER BY Name, passportID
                """
            )
            staff_members = cursor.fetchall()

            cursor.execute(
                """
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
                ORDER BY p.PaymentID DESC
                LIMIT 10
                """
            )
            payments = cursor.fetchall()
    finally:
        conn.close()

    return {
        "visitors": visitors,
        "staff_members": staff_members,
        "payments": payments,
    }


def fetch_ticket_form_data():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    EventID AS value,
                    CONCAT(Name, ' | ', DATE_FORMAT(Date, '%Y-%m-%d %H:%i')) AS label
                FROM RaceEvent
                ORDER BY Date, EventID
                """
            )
            events = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    passportID AS value,
                    CONCAT(Name, ' | ', passportID) AS label
                FROM Visitor
                ORDER BY Name, passportID
                """
            )
            visitors = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    passportID AS value,
                    CONCAT(Name, ' | ', passportID) AS label
                FROM TicketingStaff
                ORDER BY Name, passportID
                """
            )
            staff_members = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    p.PaymentID AS value,
                    CONCAT('#', p.PaymentID, ' | ', p.Status, ' | ', p.Amount) AS label
                FROM Payment p
                LEFT JOIN RaceTicket rt
                  ON rt.PaymentID = p.PaymentID
                WHERE rt.PaymentID IS NULL
                ORDER BY p.PaymentID
                """
            )
            available_payments = cursor.fetchall()

            cursor.execute(
                """
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
                    rt.PaymentID
                FROM RaceTicket rt
                JOIN RaceEvent re
                  ON re.EventID = rt.EventID
                JOIN Visitor v
                  ON v.passportID = rt.OwnerPassportID
                ORDER BY rt.RegisteredAt DESC, rt.EventID DESC, rt.TicketID DESC
                LIMIT 10
                """
            )
            tickets = cursor.fetchall()
    finally:
        conn.close()

    return {
        "events": events,
        "visitors": visitors,
        "staff_members": staff_members,
        "available_payments": available_payments,
        "tickets": tickets,
    }


def fetch_ticket_record_form_data():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    rt.TicketID,
                    rt.EventID,
                    CONCAT(rt.TicketID, ' | ', re.Name, ' | ', rt.Status) AS label
                FROM RaceTicket rt
                JOIN RaceEvent re
                  ON re.EventID = rt.EventID
                ORDER BY rt.EventID, rt.TicketID
                """
            )
            tickets = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    rt.TicketID,
                    rt.EventID,
                    re.Name AS EventName,
                    rt.Status,
                    rt.RegisteredAt,
                    rt.UsedAt,
                    rt.OwnerPassportID,
                    v.Name AS OwnerName,
                    rt.PaymentID
                FROM RaceTicket rt
                JOIN RaceEvent re
                  ON re.EventID = rt.EventID
                JOIN Visitor v
                  ON v.passportID = rt.OwnerPassportID
                ORDER BY rt.EventID, rt.TicketID
                LIMIT 10
                """
            )
            records = cursor.fetchall()
    finally:
        conn.close()

    return {"tickets": tickets, "records": records}


def fetch_brand_form_data():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    b.Name,
                    b.Logo,
                    COUNT(bre.EventID) AS linked_events
                FROM Brand b
                LEFT JOIN Brand_RaceEvent bre
                  ON bre.BrandName = b.Name
                GROUP BY b.Name, b.Logo
                ORDER BY b.Name
                """
            )
            brands = cursor.fetchall()
    finally:
        conn.close()

    return {"brands": brands}
