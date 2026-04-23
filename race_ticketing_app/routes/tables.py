import pymysql
from flask import flash, redirect, render_template, request, url_for

from ..db import get_connection
from ..metadata import TABLE_VIEWS
from ..services.tables import fetch_form_options, fetch_record, fetch_table_rows
from ..table_utils import (
    build_row_query,
    build_where_clause,
    collect_form_data,
    get_original_primary_key_values,
    get_primary_key_values,
    get_table_config,
)


def register_table_routes(app):
    @app.route("/tables/<view_name>")
    def table_view(view_name):
        table_config, columns, rows = fetch_table_rows(view_name)
        form_options = fetch_form_options(view_name)
        return render_template(
            "table_view.html",
            table_view=table_config,
            view_name=view_name,
            columns=columns,
            rows=rows,
            table_views=TABLE_VIEWS,
            form_options=form_options,
            build_row_query=build_row_query,
            form_values={},
        )

    @app.route("/tables/<view_name>/edit")
    def edit_entry(view_name):
        table_config = get_table_config(view_name)
        key_values = get_primary_key_values(table_config, request.args)
        record = fetch_record(view_name, key_values)
        form_options = fetch_form_options(view_name)
        return render_template(
            "record_form.html",
            table_view=table_config,
            view_name=view_name,
            table_views=TABLE_VIEWS,
            form_options=form_options,
            form_values=record,
            original_key=key_values,
        )

    @app.route("/tables/<view_name>/create", methods=["POST"])
    def create_entry(view_name):
        table_config = get_table_config(view_name)

        try:
            values = collect_form_data(table_config, request.form)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("table_view", view_name=view_name))

        columns = list(values.keys())
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"""
            INSERT INTO {table_config["db_table"]} ({", ".join(columns)})
            VALUES ({placeholders})
        """

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, [values[column] for column in columns])
            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            flash(f"Create failed: {exc}", "error")
        else:
            flash(f"{table_config['title']} entry created.", "ok")
        finally:
            conn.close()

        return redirect(url_for("table_view", view_name=view_name))

    @app.route("/tables/<view_name>/update", methods=["POST"])
    def update_entry(view_name):
        table_config = get_table_config(view_name)
        original_key = {}

        try:
            original_key = get_original_primary_key_values(table_config, request.form)
            values = collect_form_data(table_config, request.form)
        except ValueError as exc:
            flash(str(exc), "error")
            if original_key:
                return redirect(url_for("edit_entry", view_name=view_name, **original_key))
            return redirect(url_for("table_view", view_name=view_name))

        assignments = ", ".join(f"{column} = %s" for column in values.keys())
        query = f"""
            UPDATE {table_config["db_table"]}
            SET {assignments}
            WHERE {build_where_clause(table_config["primary_key"])}
        """
        params = [values[column] for column in values.keys()] + [
            original_key[column] for column in table_config["primary_key"]
        ]

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            flash(f"Update failed: {exc}", "error")
            redirect_key = {column: original_key[column] for column in table_config["primary_key"]}
            return redirect(url_for("edit_entry", view_name=view_name, **redirect_key))
        finally:
            conn.close()

        flash(f"{table_config['title']} entry updated.", "ok")
        return redirect(url_for("table_view", view_name=view_name))

    @app.route("/tables/<view_name>/delete", methods=["POST"])
    def delete_entry(view_name):
        table_config = get_table_config(view_name)

        try:
            key_values = get_primary_key_values(table_config, request.form)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("table_view", view_name=view_name))

        query = f"""
            DELETE FROM {table_config["db_table"]}
            WHERE {build_where_clause(table_config["primary_key"])}
        """

        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, [key_values[column] for column in table_config["primary_key"]])
            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            flash(f"Delete failed: {exc}", "error")
        else:
            flash(f"{table_config['title']} entry deleted.", "ok")
        finally:
            conn.close()

        return redirect(url_for("table_view", view_name=view_name))
