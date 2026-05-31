from __future__ import annotations

import hashlib
from typing import Any

import requests
import streamlit as st

from config.settings import ga4_api_secret, ga4_measurement_id, has_ga4_config


class AnalyticsService:
    def __init__(self) -> None:
        self.enabled = has_ga4_config()

    @staticmethod
    def client_id_from_email(email: str) -> str:
        if not email:
            return "anonymous"
        digest = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()
        return f"{digest[:10]}.{digest[10:20]}"

    def track(self, event_name: str, email: str = "", params: dict[str, Any] | None = None) -> None:
        if not self.enabled:
            return

        payload = {
            "client_id": self.client_id_from_email(email),
            "events": [{"name": event_name, "params": params or {}}],
        }

        url = (
            "https://www.google-analytics.com/mp/collect"
            f"?measurement_id={ga4_measurement_id()}&api_secret={ga4_api_secret()}"
        )

        try:
            requests.post(url, json=payload, timeout=3)
        except Exception:
            pass


@st.cache_resource
def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()
