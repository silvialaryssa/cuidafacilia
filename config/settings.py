from __future__ import annotations

import streamlit as st


def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name)

        if value is None:
            return default

        return str(value).strip()

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


def chatgpt_api_key() -> str:
    return get_secret("chatgpt_api_key", "").strip()


def chatgpt_model() -> str:
    return get_secret("chatgpt_model", "gpt-4.1-mini").strip() or "gpt-4.1-mini"


def chatgpt_api_base_url() -> str:
    return get_secret("chatgpt_api_base_url", "https://api.openai.com/v1").strip().rstrip("/")


def has_google_sheets_config() -> bool:
    try:
        return bool(spreadsheet_id() and st.secrets.get("gcp_service_account"))
    except Exception:
        return False


def has_ga4_config() -> bool:
    return bool(ga4_measurement_id() and ga4_api_secret())


def has_chatgpt_config() -> bool:
    return bool(chatgpt_api_key())

#def gemini_api_key() -> str:
    #return get_secret("gemini_api_key", "AIzaSyA_vxb6aTVPCSpi_Al2eU80FO5NupLLf-o").strip()

def gemini_api_key() -> str:
    return get_secret("gemini_api_key", "").strip()


def gemini_model() -> str:
    return get_secret("gemini_model", "gemini-2.5-flash").strip() or "gemini-2.5-flash"


def gemini_api_base_url() -> str:
    return get_secret(
        "gemini_api_base_url",
        "https://generativelanguage.googleapis.com/v1beta",
    ).strip().rstrip("/")


def default_ai_provider() -> str:
    provider = get_secret("ai_provider", "gemini").strip().lower()
    return provider if provider in {"openai", "gemini"} else "gemini"


def default_ai_model() -> str:
    provider = default_ai_provider()
    return chatgpt_model() if provider == "openai" else gemini_model()


def has_gemini_config() -> bool:
    return bool(gemini_api_key())


def has_ai_config() -> bool:
    provider = default_ai_provider()
    if provider == "openai":
        return has_chatgpt_config()
    return has_gemini_config()
