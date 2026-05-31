from __future__ import annotations

import streamlit as st


def get_secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def admin_email() -> str:
    return get_secret("admin_email", "admin@cuidafacil.com").strip().lower()


def spreadsheet_id() -> str:
    return get_secret("spreadsheet_id", "").strip()


def ga4_measurement_id() -> str:
    return get_secret("ga4_measurement_id", "").strip()


def ga4_api_secret() -> str:
    return get_secret("ga4_api_secret", "").strip()


def has_google_sheets_config() -> bool:
    try:
        return bool(spreadsheet_id() and st.secrets.get("gcp_service_account"))
    except Exception:
        return False


def has_ga4_config() -> bool:
    return bool(ga4_measurement_id() and ga4_api_secret())
