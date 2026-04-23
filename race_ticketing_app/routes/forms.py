from datetime import datetime
from decimal import Decimal, InvalidOperation

import pymysql
from flask import flash, redirect, render_template, request, url_for

from ..db import get_connection
from ..services.forms_data import (
    fetch_brand_form_data,
    fetch_payment_form_data,
    fetch_ticket_form_data,
    fetch_ticket_record_form_data,
)


def register_form_routes(app):
    @app.route("/forms/payment-confirmation")
    def payment_confirmation_form():
        return render_template("payment_confirmation_form.html", data=fetch_payment_form_data())

    @app.route("/forms/payment-confirmation/create", methods=["POST"])
    def create_payment_confirmation():
        status = request.form.get("status", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        confirmation_date = request.form.get("confirmation_date", "").strip() or None
        visitor_passport = request.form.get("visitor_passport_id", "").strip()
        staff_passport = request.form.get("staff_passport_id", "").strip()

        if not all([status, amount_raw, visitor_passport, staff_passport]):
            flash("Payment confirmation create form requires status, amount, visitor, and staff.", "error")
            return redirect(url_for("payment_confirmation_form"))

        try:
            amount = Decimal(amount_raw)
            if confirmation_date:
                confirmation_date = datetime.fromisoformat(confirmation_date).strftime("%Y-%m-%d %H:%M:%S")
        except (InvalidOperation, ValueError):
            flash("Payment confirmation create form contains invalid numeric or date values.", "error")
            return redirect(url_for("payment_confirmation_form"))

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO Payment (Status, Amount, ConfirmationDate, VisitorPassportID, StaffPassportID)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (status, amount, confirmation_date, visitor_passport, staff_passport),
                )
            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            flash(f"Payment create failed: {exc}", "error")
        else:
            flash("Payment confirmation added.", "ok")
        finally:
            conn.close()

        return redirect(url_for("payment_confirmation_form"))

    @app.route("/forms/payment-confirmation/update", methods=["POST"])
    def update_payment_confirmation():
        payment_id = request.form.get("payment_id", "").strip()
        status = request.form.get("status", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        confirmation_date = request.form.get("confirmation_date", "").strip() or None
        visitor_passport = request.form.get("visitor_passport_id", "").strip()
        staff_passport = request.form.get("staff_passport_id", "").strip()

        if not all([payment_id, status, amount_raw, visitor_passport, staff_passport]):
            flash("Payment confirmation update form requires payment id, status, amount, visitor, and staff.", "error")
            return redirect(url_for("payment_confirmation_form"))

        try:
            payment_id = int(payment_id)
            amount = Decimal(amount_raw)
            if confirmation_date:
                confirmation_date = datetime.fromisoformat(confirmation_date).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, InvalidOperation):
            flash("Payment confirmation update form contains invalid numeric or date values.", "error")
            return redirect(url_for("payment_confirmation_form"))

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE Payment
                    SET Status = %s,
                        Amount = %s,
                        ConfirmationDate = %s,
                        VisitorPassportID = %s,
                        StaffPassportID = %s
                    WHERE PaymentID = %s
                    """,
                    (status, amount, confirmation_date, visitor_passport, staff_passport, payment_id),
                )
            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            flash(f"Payment update failed: {exc}", "error")
        else:
            flash("Payment confirmation updated.", "ok")
        finally:
            conn.close()

        return redirect(url_for("payment_confirmation_form"))

    @app.route("/forms/printed-ticket")
    def printed_ticket_form():
        return render_template("printed_ticket_form.html", data=fetch_ticket_form_data())

    @app.route("/forms/printed-ticket/create", methods=["POST"])
    def create_printed_ticket():
        ticket_id = request.form.get("ticket_id", "").strip()
        event_id = request.form.get("event_id", "").strip()
        owner_passport = request.form.get("owner_passport_id", "").strip()
        payment_id = request.form.get("payment_id", "").strip()
        staff_passport = request.form.get("staff_passport_id", "").strip()
        price_raw = request.form.get("price", "").strip()
        registered_at = request.form.get("registered_at", "").strip() or None
        status = request.form.get("status", "").strip() or "Registered"

        if not all([ticket_id, event_id, owner_passport, payment_id, staff_passport, price_raw]):
            flash("Printed ticket form requires ticket id, event, owner, payment, staff, and price.", "error")
            return redirect(url_for("printed_ticket_form"))

        try:
            event_id = int(event_id)
            payment_id = int(payment_id)
            price = Decimal(price_raw)
            if registered_at:
                registered_at = datetime.fromisoformat(registered_at).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, InvalidOperation):
            flash("Printed ticket form contains invalid numeric or date values.", "error")
            return redirect(url_for("printed_ticket_form"))

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO RaceTicket (
                        TicketID, Price, RegisteredAt, UsedAt, Status,
                        EventID, OwnerPassportID, PaymentID, RegisteredByStaffPassportID
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (ticket_id, price, registered_at, None, status, event_id, owner_passport, payment_id, staff_passport),
                )
            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            flash(f"Printed ticket create failed: {exc}", "error")
        else:
            flash("Printed ticket added.", "ok")
        finally:
            conn.close()

        return redirect(url_for("printed_ticket_form"))

    @app.route("/forms/ticket-record")
    def ticket_record_form():
        return render_template("ticket_record_form.html", data=fetch_ticket_record_form_data())

    @app.route("/forms/ticket-record/update", methods=["POST"])
    def update_ticket_record():
        ticket_id = request.form.get("ticket_id", "").strip()
        event_id = request.form.get("event_id", "").strip()
        status = request.form.get("status", "").strip()
        used_at = request.form.get("used_at", "").strip() or None

        if not all([ticket_id, event_id, status]):
            flash("Ticket record update requires ticket id, event id, and status.", "error")
            return redirect(url_for("ticket_record_form"))

        try:
            event_id = int(event_id)
            if used_at:
                used_at = datetime.fromisoformat(used_at).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            flash("Ticket record update contains an invalid date or event id.", "error")
            return redirect(url_for("ticket_record_form"))

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE RaceTicket
                    SET Status = %s, UsedAt = %s
                    WHERE TicketID = %s AND EventID = %s
                    """,
                    (status, used_at, ticket_id, event_id),
                )
            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            flash(f"Ticket record update failed: {exc}", "error")
        else:
            flash("Ticket record updated.", "ok")
        finally:
            conn.close()

        return redirect(url_for("ticket_record_form"))

    @app.route("/forms/ticket-record/delete", methods=["POST"])
    def delete_ticket_record():
        ticket_id = request.form.get("ticket_id", "").strip()
        event_id = request.form.get("event_id", "").strip()

        if not all([ticket_id, event_id]):
            flash("Ticket record delete requires ticket id and event id.", "error")
            return redirect(url_for("ticket_record_form"))

        try:
            event_id = int(event_id)
        except ValueError:
            flash("Ticket record delete contains an invalid event id.", "error")
            return redirect(url_for("ticket_record_form"))

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM RaceTicket
                    WHERE TicketID = %s AND EventID = %s
                    """,
                    (ticket_id, event_id),
                )
            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            flash(f"Ticket record delete failed: {exc}", "error")
        else:
            flash("Ticket record deleted.", "ok")
        finally:
            conn.close()

        return redirect(url_for("ticket_record_form"))

    @app.route("/forms/brand-profile")
    def brand_profile_form():
        return render_template("brand_profile_form.html", data=fetch_brand_form_data())

    @app.route("/forms/brand-profile/create", methods=["POST"])
    def create_brand_profile():
        name = request.form.get("name", "").strip()
        logo = request.form.get("logo", "").strip() or None

        if not name:
            flash("Brand create requires a name.", "error")
            return redirect(url_for("brand_profile_form"))

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO Brand (Name, Logo) VALUES (%s, %s)", (name, logo))
            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            flash(f"Brand create failed: {exc}", "error")
        else:
            flash("Brand profile added.", "ok")
        finally:
            conn.close()

        return redirect(url_for("brand_profile_form"))

    @app.route("/forms/brand-profile/update", methods=["POST"])
    def update_brand_profile():
        original_name = request.form.get("original_name", "").strip()
        new_name = request.form.get("new_name", "").strip()
        logo = request.form.get("logo", "").strip() or None

        if not all([original_name, new_name]):
            flash("Brand update requires original and new name.", "error")
            return redirect(url_for("brand_profile_form"))

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE Brand
                    SET Name = %s, Logo = %s
                    WHERE Name = %s
                    """,
                    (new_name, logo, original_name),
                )
            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            flash(f"Brand update failed: {exc}", "error")
        else:
            flash("Brand profile updated. Junction rows follow through cascade update.", "ok")
        finally:
            conn.close()

        return redirect(url_for("brand_profile_form"))

    @app.route("/forms/brand-profile/delete", methods=["POST"])
    def delete_brand_profile():
        name = request.form.get("name", "").strip()

        if not name:
            flash("Brand delete requires a name.", "error")
            return redirect(url_for("brand_profile_form"))

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM Brand WHERE Name = %s", (name,))
            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            flash(f"Brand delete failed: {exc}", "error")
        else:
            flash("Brand profile deleted. Linked Brand_RaceEvent rows were removed by cascade.", "ok")
        finally:
            conn.close()

        return redirect(url_for("brand_profile_form"))
