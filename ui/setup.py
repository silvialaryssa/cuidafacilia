from __future__ import annotations

import streamlit as st

from config.settings import (
    chatgpt_model,

    gemini_model,
    has_chatgpt_config,
    has_gemini_config,
    has_ga4_config,
    has_google_sheets_config,
    spreadsheet_id,
)
from services.app_service import repository_status
from ui.components import figure_card


def render_setup() -> None:
    
    from config.settings import (
    gemini_api_key,
    chatgpt_api_key,
    default_ai_provider,
)

    st.subheader("🔍 Diagnóstico IA")

    st.write("Secrets carregados:")
    st.write(list(st.secrets.keys()))

    st.write("Gemini:", bool(gemini_api_key()))
    st.write("OpenAI:", bool(chatgpt_api_key()))
    st.write("Provider:", default_ai_provider())
        
    st.subheader("Configuração inicial")
    st.markdown(
        """
        <div class="section-intro">
            Configure as integrações em poucos passos para liberar analytics, dados e IA no aplicativo.
        </div>
        """,
        unsafe_allow_html=True,
    )

    info_col1, info_col2 = st.columns(2)
    with info_col1:
        figure_card("🧩", "Integrações", "Google Sheets e GA4 podem funcionar juntos para visão completa do uso.")
    with info_col2:
        figure_card("🤖", "Assistente de plantas", "Configure a chave da API para ativar o Cuidador IA de Plantas.")

    status = repository_status()

    col1, col2, col3 = st.columns(3)

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

    with col3:
        st.markdown("### IA do Cuidador")
        if has_gemini_config() or has_chatgpt_config():
            st.success("IA configurada.")
            if has_gemini_config():
                st.caption(f"Gemini disponível: {gemini_model()}")
            if has_chatgpt_config():
                st.caption(f"OpenAI disponível: {chatgpt_model()}")
        else:
            st.info("Nenhuma API de IA configurada. A funcionalidade de IA ficará desativada.")

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
# IA - escolha padrão inicial; a área Admin pode trocar depois
ai_provider = "gemini"

# Google Gemini
gemini_api_key = "SUA_CHAVE_GEMINI"
gemini_model = "gemini-2.5-flash"
gemini_api_base_url = "https://generativelanguage.googleapis.com/v1beta"

# OpenAI / ChatGPT
chatgpt_api_key = "sk-..."
chatgpt_model = "gpt-4.1-mini"
chatgpt_api_base_url = "https://api.openai.com/v1"

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
