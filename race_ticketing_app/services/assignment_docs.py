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


def fetch_assignment_docs():
    docs = []
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT passportID FROM Visitor ORDER BY passportID LIMIT 1")
            visitor = cursor.fetchone()
            cursor.execute("SELECT passportID FROM TicketingStaff ORDER BY passportID LIMIT 1")
            staff = cursor.fetchone()
            cursor.execute("SELECT EventID FROM RaceEvent ORDER BY EventID LIMIT 1")
            event = cursor.fetchone()
            cursor.execute(
                """
                SELECT TicketID, EventID
                FROM RaceTicket
                ORDER BY EventID, TicketID
                LIMIT 1
                """
            )
            ticket = cursor.fetchone()
            cursor.execute(
                """
                SELECT b.Name
                FROM Brand b
                JOIN Brand_RaceEvent bre
                  ON bre.BrandName = b.Name
                GROUP BY b.Name
                ORDER BY b.Name
                LIMIT 1
                """
            )
            brand = cursor.fetchone()

            if visitor and staff:
                cursor.execute(
                    """
                    SELECT PaymentID, Status, Amount, ConfirmationDate, VisitorPassportID, StaffPassportID
                    FROM Payment
                    ORDER BY PaymentID DESC
                    LIMIT 3
                    """
                )
                before = serialize_rows(cursor.fetchall())
                cursor.execute(
                    """
                    INSERT INTO Payment (Status, Amount, ConfirmationDate, VisitorPassportID, StaffPassportID)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    ("Confirmed", Decimal("321.45"), "2026-11-15 09:30:00", visitor["passportID"], staff["passportID"]),
                )
                new_payment_id = cursor.lastrowid
                cursor.execute(
                    """
                    SELECT PaymentID, Status, Amount, ConfirmationDate, VisitorPassportID, StaffPassportID
                    FROM Payment
                    WHERE PaymentID IN (%s)
                    """,
                    (new_payment_id,),
                )
                after = serialize_rows(cursor.fetchall())
                conn.rollback()
                docs.append(
                    {
                        "form_title": "Document A: Payment Confirmation",
                        "mapping_note": "The deployed schema stores payment status, amount, confirmation date, visitor, and staff. `transaction_id` from the input document is not present in the current database design.",
                        "operations": [
                            {
                                "title": "Add New Payment Confirmation",
                                "sql": [
                                    """
INSERT INTO Payment (Status, Amount, ConfirmationDate, VisitorPassportID, StaffPassportID)
VALUES ('Confirmed', 321.45, '2026-11-15 09:30:00', '<visitor_passport>', '<staff_passport>');
                                    """.strip()
                                ],
                                "before_tables": [{"name": "Payment", "rows": before}],
                                "after_tables": [{"name": "Payment", "rows": after}],
                            }
                        ],
                    }
                )

            if visitor and staff and event:
                cursor.execute(
                    """
                    SELECT PaymentID
                    FROM Payment p
                    LEFT JOIN RaceTicket rt
                      ON rt.PaymentID = p.PaymentID
                    WHERE rt.PaymentID IS NULL
                    ORDER BY PaymentID
                    LIMIT 1
                    """
                )
                available_payment = cursor.fetchone()
                prerequisite_sql = []
                if not available_payment:
                    cursor.execute(
                        """
                        INSERT INTO Payment (Status, Amount, ConfirmationDate, VisitorPassportID, StaffPassportID)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        ("Confirmed", Decimal("299.00"), "2026-11-15 10:00:00", visitor["passportID"], staff["passportID"]),
                    )
                    available_payment = {"PaymentID": cursor.lastrowid}
                    prerequisite_sql.append(
                        """
INSERT INTO Payment (Status, Amount, ConfirmationDate, VisitorPassportID, StaffPassportID)
VALUES ('Confirmed', 299.00, '2026-11-15 10:00:00', '<visitor_passport>', '<staff_passport>');
                        """.strip()
                    )

                cursor.execute(
                    """
                    SELECT TicketID, EventID, Price, RegisteredAt, UsedAt, Status, OwnerPassportID, PaymentID, RegisteredByStaffPassportID
                    FROM RaceTicket
                    ORDER BY EventID, TicketID
                    LIMIT 3
                    """
                )
                before = serialize_rows(cursor.fetchall())
                cursor.execute(
                    """
                    INSERT INTO RaceTicket (
                        TicketID, Price, RegisteredAt, UsedAt, Status,
                        EventID, OwnerPassportID, PaymentID, RegisteredByStaffPassportID
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        "DOC-TMP-001",
                        Decimal("299.00"),
                        "2026-11-15 10:05:00",
                        None,
                        "Registered",
                        event["EventID"],
                        visitor["passportID"],
                        available_payment["PaymentID"],
                        staff["passportID"],
                    ),
                )
                cursor.execute(
                    """
                    SELECT TicketID, EventID, Price, RegisteredAt, UsedAt, Status, OwnerPassportID, PaymentID, RegisteredByStaffPassportID
                    FROM RaceTicket
                    WHERE TicketID = %s AND EventID = %s
                    """,
                    ("DOC-TMP-001", event["EventID"]),
                )
                after = serialize_rows(cursor.fetchall())
                conn.rollback()
                docs.append(
                    {
                        "form_title": "Document B: Ticket / Printed Ticket",
                        "mapping_note": "The deployed schema persists `TicketID`, `EventID`, owner, price, registration time, payment, and responsible staff. `seat_number` and `ticket_type` are not present in the current `RaceTicket` table, while the printed ticket date is derived from the selected race event.",
                        "operations": [
                            {
                                "title": "Add New Printed Ticket",
                                "sql": prerequisite_sql
                                + [
                                    """
INSERT INTO RaceTicket (
    TicketID, Price, RegisteredAt, UsedAt, Status,
    EventID, OwnerPassportID, PaymentID, RegisteredByStaffPassportID
)
VALUES (
    'DOC-TMP-001', 299.00, '2026-11-15 10:05:00', NULL, 'Registered',
    <event_id>, '<visitor_passport>', <payment_id>, '<staff_passport>'
);
                                    """.strip()
                                ],
                                "before_tables": [{"name": "RaceTicket", "rows": before}],
                                "after_tables": [{"name": "RaceTicket", "rows": after}],
                            }
                        ],
                    }
                )

            if ticket:
                cursor.execute(
                    """
                    SELECT TicketID, EventID, Status, RegisteredAt, UsedAt, PaymentID
                    FROM RaceTicket
                    WHERE TicketID = %s AND EventID = %s
                    """,
                    (ticket["TicketID"], ticket["EventID"]),
                )
                update_before = serialize_rows(cursor.fetchall())
                cursor.execute(
                    """
                    UPDATE RaceTicket
                    SET Status = %s, UsedAt = %s
                    WHERE TicketID = %s AND EventID = %s
                    """,
                    ("Cancelled", None, ticket["TicketID"], ticket["EventID"]),
                )
                cursor.execute(
                    """
                    SELECT TicketID, EventID, Status, RegisteredAt, UsedAt, PaymentID
                    FROM RaceTicket
                    WHERE TicketID = %s AND EventID = %s
                    """,
                    (ticket["TicketID"], ticket["EventID"]),
                )
                update_after = serialize_rows(cursor.fetchall())
                conn.rollback()

                cursor.execute(
                    """
                    SELECT TicketID, EventID, Status, RegisteredAt, UsedAt, PaymentID
                    FROM RaceTicket
                    WHERE TicketID = %s AND EventID = %s
                    """,
                    (ticket["TicketID"], ticket["EventID"]),
                )
                delete_before = serialize_rows(cursor.fetchall())
                cursor.execute(
                    """
                    DELETE FROM RaceTicket
                    WHERE TicketID = %s AND EventID = %s
                    """,
                    (ticket["TicketID"], ticket["EventID"]),
                )
                cursor.execute(
                    """
                    SELECT TicketID, EventID, Status, RegisteredAt, UsedAt, PaymentID
                    FROM RaceTicket
                    WHERE TicketID = %s AND EventID = %s
                    """,
                    (ticket["TicketID"], ticket["EventID"]),
                )
                delete_after = serialize_rows(cursor.fetchall())
                conn.rollback()
                docs.append(
                    {
                        "form_title": "Document C: Ticket Record",
                        "mapping_note": "The current schema does not include a separate `TicketRecord` entity. The document maps to the existing `RaceTicket` row, using `(TicketID, EventID)` as the record key and `RegisteredAt` as the creation timestamp.",
                        "operations": [
                            {
                                "title": "Update Existing Ticket Record",
                                "sql": [
                                    """
UPDATE RaceTicket
SET Status = 'Cancelled', UsedAt = NULL
WHERE TicketID = '<ticket_id>' AND EventID = <event_id>;
                                    """.strip()
                                ],
                                "before_tables": [{"name": "RaceTicket", "rows": update_before}],
                                "after_tables": [{"name": "RaceTicket", "rows": update_after}],
                            },
                            {
                                "title": "Delete Existing Ticket Record",
                                "sql": [
                                    """
DELETE FROM RaceTicket
WHERE TicketID = '<ticket_id>' AND EventID = <event_id>;
                                    """.strip()
                                ],
                                "before_tables": [{"name": "RaceTicket", "rows": delete_before}],
                                "after_tables": [{"name": "RaceTicket", "rows": delete_after}],
                            },
                        ],
                    }
                )

            if brand:
                cursor.execute(
                    """
                    SELECT Name, Logo
                    FROM Brand
                    WHERE Name = %s
                    """,
                    (brand["Name"],),
                )
                brand_before = serialize_rows(cursor.fetchall())
                cursor.execute(
                    """
                    SELECT BrandName, EventID
                    FROM Brand_RaceEvent
                    WHERE BrandName = %s
                    ORDER BY EventID
                    """,
                    (brand["Name"],),
                )
                links_before = serialize_rows(cursor.fetchall())
                renamed_brand = f"{brand['Name']}_TMP"
                cursor.execute(
                    """
                    UPDATE Brand
                    SET Name = %s
                    WHERE Name = %s
                    """,
                    (renamed_brand, brand["Name"]),
                )
                cursor.execute(
                    """
                    SELECT Name, Logo
                    FROM Brand
                    WHERE Name = %s
                    """,
                    (renamed_brand,),
                )
                brand_after = serialize_rows(cursor.fetchall())
                cursor.execute(
                    """
                    SELECT BrandName, EventID
                    FROM Brand_RaceEvent
                    WHERE BrandName = %s
                    ORDER BY EventID
                    """,
                    (renamed_brand,),
                )
                links_after = serialize_rows(cursor.fetchall())
                conn.rollback()

                cursor.execute(
                    """
                    SELECT Name, Logo
                    FROM Brand
                    WHERE Name = %s
                    """,
                    (brand["Name"],),
                )
                delete_brand_before = serialize_rows(cursor.fetchall())
                cursor.execute(
                    """
                    SELECT BrandName, EventID
                    FROM Brand_RaceEvent
                    WHERE BrandName = %s
                    ORDER BY EventID
                    """,
                    (brand["Name"],),
                )
                delete_links_before = serialize_rows(cursor.fetchall())
                cursor.execute("DELETE FROM Brand WHERE Name = %s", (brand["Name"],))
                cursor.execute(
                    """
                    SELECT Name, Logo
                    FROM Brand
                    WHERE Name = %s
                    """,
                    (brand["Name"],),
                )
                delete_brand_after = serialize_rows(cursor.fetchall())
                cursor.execute(
                    """
                    SELECT BrandName, EventID
                    FROM Brand_RaceEvent
                    WHERE BrandName = %s
                    ORDER BY EventID
                    """,
                    (brand["Name"],),
                )
                delete_links_after = serialize_rows(cursor.fetchall())
                conn.rollback()
                docs.append(
                    {
                        "form_title": "Additional Form: Brand Profile",
                        "mapping_note": "This form is included because the deployed schema demonstrates `ON UPDATE CASCADE` and `ON DELETE CASCADE` through `Brand -> Brand_RaceEvent`. The ticketing documents alone cannot demonstrate cascade deletion on the live schema.",
                        "operations": [
                            {
                                "title": "Cascade Update of Brand Name",
                                "sql": [
                                    """
UPDATE Brand
SET Name = '<new_brand_name>'
WHERE Name = '<old_brand_name>';
                                    """.strip()
                                ],
                                "before_tables": [
                                    {"name": "Brand", "rows": brand_before},
                                    {"name": "Brand_RaceEvent", "rows": links_before},
                                ],
                                "after_tables": [
                                    {"name": "Brand", "rows": brand_after},
                                    {"name": "Brand_RaceEvent", "rows": links_after},
                                ],
                            },
                            {
                                "title": "Cascade Delete of Brand",
                                "sql": [
                                    """
DELETE FROM Brand
WHERE Name = '<brand_name>';
                                    """.strip()
                                ],
                                "before_tables": [
                                    {"name": "Brand", "rows": delete_brand_before},
                                    {"name": "Brand_RaceEvent", "rows": delete_links_before},
                                ],
                                "after_tables": [
                                    {"name": "Brand", "rows": delete_brand_after},
                                    {"name": "Brand_RaceEvent", "rows": delete_links_after},
                                ],
                            },
                        ],
                    }
                )
    finally:
        conn.rollback()
        conn.close()

    return docs
