TABLE_VIEWS = {
    "brands": {
        "title": "Brands",
        "description": "Organizer brands participating in motorsport events.",
        "db_table": "Brand",
        "primary_key": ["Name"],
        "fields": [
            {"name": "Name", "label": "Name", "type": "text", "required": True},
            {"name": "Logo", "label": "Logo", "type": "text", "required": False},
        ],
        "list_query": """
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
        "db_table": "RaceEvent",
        "primary_key": ["EventID"],
        "fields": [
            {"name": "EventID", "label": "Event ID", "type": "integer", "auto_increment": True},
            {"name": "Name", "label": "Name", "type": "text", "required": True},
            {"name": "Description", "label": "Description", "type": "textarea", "required": False},
            {"name": "Date", "label": "Date", "type": "datetime-local", "required": True},
            {"name": "Location", "label": "Location", "type": "text", "required": False},
        ],
        "list_query": """
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
        "db_table": "Brand_RaceEvent",
        "primary_key": ["BrandName", "EventID"],
        "fields": [
            {
                "name": "BrandName",
                "label": "Brand",
                "type": "select",
                "required": True,
                "options_query": """
                    SELECT Name AS value, Name AS label
                    FROM Brand
                    ORDER BY Name
                """,
            },
            {
                "name": "EventID",
                "label": "Event",
                "type": "select",
                "required": True,
                "options_query": """
                    SELECT
                        EventID AS value,
                        CONCAT(Name, ' | ', DATE_FORMAT(Date, '%Y-%m-%d %H:%i')) AS label
                    FROM RaceEvent
                    ORDER BY Date, EventID
                """,
            },
        ],
        "list_query": """
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
        "db_table": "Visitor",
        "primary_key": ["passportID"],
        "fields": [
            {"name": "passportID", "label": "Passport ID", "type": "text", "required": True},
            {"name": "Name", "label": "Name", "type": "text", "required": True},
            {"name": "Email", "label": "Email", "type": "email", "required": False},
            {"name": "Phone", "label": "Phone", "type": "text", "required": False},
        ],
        "list_query": """
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
        "db_table": "TicketingStaff",
        "primary_key": ["passportID"],
        "fields": [
            {"name": "passportID", "label": "Passport ID", "type": "text", "required": True},
            {"name": "Name", "label": "Name", "type": "text", "required": True},
        ],
        "list_query": """
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
        "db_table": "Payment",
        "primary_key": ["PaymentID"],
        "fields": [
            {"name": "PaymentID", "label": "Payment ID", "type": "integer", "auto_increment": True},
            {"name": "Status", "label": "Status", "type": "text", "required": True},
            {"name": "Amount", "label": "Amount", "type": "decimal", "required": True},
            {"name": "ConfirmationDate", "label": "Confirmation Date", "type": "datetime-local", "required": False},
            {
                "name": "VisitorPassportID",
                "label": "Visitor",
                "type": "select",
                "required": True,
                "options_query": """
                    SELECT
                        passportID AS value,
                        CONCAT(Name, ' | ', passportID) AS label
                    FROM Visitor
                    ORDER BY Name, passportID
                """,
            },
            {
                "name": "StaffPassportID",
                "label": "Ticketing Staff",
                "type": "select",
                "required": True,
                "options_query": """
                    SELECT
                        passportID AS value,
                        CONCAT(Name, ' | ', passportID) AS label
                    FROM TicketingStaff
                    ORDER BY Name, passportID
                """,
            },
        ],
        "list_query": """
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
        "db_table": "RaceTicket",
        "primary_key": ["TicketID", "EventID"],
        "fields": [
            {"name": "TicketID", "label": "Ticket ID", "type": "text", "required": True},
            {"name": "Price", "label": "Price", "type": "decimal", "required": True},
            {"name": "RegisteredAt", "label": "Registered At", "type": "datetime-local", "required": False},
            {"name": "UsedAt", "label": "Used At", "type": "datetime-local", "required": False},
            {"name": "Status", "label": "Status", "type": "text", "required": False},
            {
                "name": "EventID",
                "label": "Event",
                "type": "select",
                "required": True,
                "options_query": """
                    SELECT
                        EventID AS value,
                        CONCAT(Name, ' | ', DATE_FORMAT(Date, '%Y-%m-%d %H:%i')) AS label
                    FROM RaceEvent
                    ORDER BY Date, EventID
                """,
            },
            {
                "name": "OwnerPassportID",
                "label": "Owner",
                "type": "select",
                "required": True,
                "options_query": """
                    SELECT
                        passportID AS value,
                        CONCAT(Name, ' | ', passportID) AS label
                    FROM Visitor
                    ORDER BY Name, passportID
                """,
            },
            {
                "name": "PaymentID",
                "label": "Payment",
                "type": "select",
                "required": True,
                "options_query": """
                    SELECT
                        PaymentID AS value,
                        CONCAT('#', PaymentID, ' | ', Status, ' | ', Amount) AS label
                    FROM Payment
                    ORDER BY PaymentID
                """,
            },
            {
                "name": "RegisteredByStaffPassportID",
                "label": "Registered By Staff",
                "type": "select",
                "required": True,
                "options_query": """
                    SELECT
                        passportID AS value,
                        CONCAT(Name, ' | ', passportID) AS label
                    FROM TicketingStaff
                    ORDER BY Name, passportID
                """,
            },
        ],
        "list_query": """
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
