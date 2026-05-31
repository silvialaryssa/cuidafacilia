from __future__ import annotations

import streamlit as st

from config.settings import has_ga4_config, has_google_sheets_config, spreadsheet_id
from services.app_service import repository_status


def render_setup() -> None:
    st.subheader("Configuração inicial")

    status = repository_status()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Google Sheets")
        if has_google_sheets_config() and status.get("enabled"):
            st.success("Google Sheets configurado e conectado.")
        elif has_google_sheets_config() and not status.get("enabled"):
            st.warning("Credenciais encontradas, mas não foi possível conectar.")
            st.code(status.get("error_message", "Erro não informado."))
        else:
            st.info("Google Sheets ainda não configurado.")

        st.write("`spreadsheet_id` atual:")
        st.code(spreadsheet_id() or "não informado")

    with col2:
        st.markdown("### Google Analytics 4")
        if has_ga4_config():
            st.success("GA4 configurado.")
        else:
            st.info("GA4 ainda não configurado. O app funciona, mas sem enviar eventos.")

    st.divider()

    st.markdown("### Abas esperadas no Google Sheets")
    st.write(", ".join(status.get("required_sheets", [])))

    st.markdown("### Como configurar")
    st.code(
        '''
admin_email = "seu_email@gmail.com"
spreadsheet_id = "ID_DA_PLANILHA"
ga4_measurement_id = "G-XXXXXXXXXX"
ga4_api_secret = "API_SECRET"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
        '''.strip(),
        language="toml",
    )

    st.info("No Streamlit Cloud, cole esse conteúdo em App > Settings > Secrets.")
