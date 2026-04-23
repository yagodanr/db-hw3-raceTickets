from ..db import get_connection
from ..table_utils import build_where_clause, fetch_select_options, get_table_config


def fetch_table_rows(view_name):
    table_config = get_table_config(view_name)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(table_config["list_query"])
            rows = cursor.fetchall()
    finally:
        conn.close()

    columns = list(rows[0].keys()) if rows else []
    return table_config, columns, rows


def fetch_form_options(view_name):
    table_config = get_table_config(view_name)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            return fetch_select_options(cursor, table_config)
    finally:
        conn.close()


def fetch_record(view_name, key_values):
    table_config = get_table_config(view_name)
    field_names = [field["name"] for field in table_config["fields"]]
    query = f"""
        SELECT {", ".join(field_names)}
        FROM {table_config["db_table"]}
        WHERE {build_where_clause(table_config["primary_key"])}
    """

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, [key_values[column] for column in table_config["primary_key"]])
            record = cursor.fetchone()
    finally:
        conn.close()

    if record is None:
        from flask import abort

        abort(404)
    return record
