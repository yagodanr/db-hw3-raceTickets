from datetime import datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from flask import abort

from .metadata import TABLE_VIEWS


def get_table_config(view_name):
    table_config = TABLE_VIEWS.get(view_name)
    if table_config is None:
        abort(404)
    return table_config


def get_editable_fields(table_config, include_auto_increment=False):
    fields = table_config["fields"]
    if include_auto_increment:
        return fields
    return [field for field in fields if not field.get("auto_increment")]


def format_datetime_for_input(value):
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M")
    return str(value).replace(" ", "T")[:16]


def format_value_for_form(field, value):
    if value is None:
        return ""
    if field["type"] == "datetime-local":
        return format_datetime_for_input(value)
    return str(value)


def normalize_form_value(field, raw_value):
    raw_value = (raw_value or "").strip()
    if raw_value == "":
        if field.get("required"):
            raise ValueError(f"{field['label']} is required.")
        return None

    field_type = field["type"]
    if field_type == "integer":
        try:
            return int(raw_value)
        except ValueError as exc:
            raise ValueError(f"{field['label']} must be an integer.") from exc
    if field_type == "decimal":
        try:
            return Decimal(raw_value)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"{field['label']} must be a decimal number.") from exc
    if field_type == "datetime-local":
        try:
            return datetime.fromisoformat(raw_value).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ValueError(f"{field['label']} must be a valid date and time.") from exc
    return raw_value


def collect_form_data(table_config, source):
    values = {}
    for field in get_editable_fields(table_config):
        values[field["name"]] = normalize_form_value(field, source.get(field["name"]))
    return values


def get_primary_key_values(table_config, source):
    key_values = {}
    for column in table_config["primary_key"]:
        value = source.get(column)
        if value is None or str(value).strip() == "":
            raise ValueError(f"Missing primary key field: {column}.")
        key_values[column] = value
    return key_values


def get_original_primary_key_values(table_config, source):
    key_values = {}
    for column in table_config["primary_key"]:
        source_name = f"original__{column}"
        value = source.get(source_name)
        if value is None or str(value).strip() == "":
            raise ValueError(f"Missing original primary key field: {column}.")
        key_values[column] = value
    return key_values


def build_where_clause(columns):
    return " AND ".join(f"{column} = %s" for column in columns)


def fetch_select_options(cursor, table_config):
    options = {}
    for field in table_config["fields"]:
        if "options_query" not in field:
            continue
        cursor.execute(field["options_query"])
        option_rows = cursor.fetchall()
        options[field["name"]] = [
            {"value": str(row["value"]), "label": row["label"]} for row in option_rows
        ]
    return options


def build_row_query(table_config, row):
    return urlencode({column: row[column] for column in table_config["primary_key"]})
