from __future__ import annotations

import streamlit as st

from config.settings import admin_email
from services.app_service import (
    find_user_by_email,
    is_valid_email,
    login_existing_user,
    register_new_user,
    record_session_once,
)
from ui.admin import render_admin
from ui.components import hero, load_css, quote_card
from ui.home import render_home
from ui.landing import render_landing
from ui.plant_ai import render_plant_ai
from ui.progress import render_progress
from ui.setup import render_setup
from utils.proverbios import random_proverb


st.set_page_config(
    page_title="CuidaFácil",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()

if "proverbio" not in st.session_state:
    st.session_state["proverbio"] = random_proverb()

with st.sidebar:
    st.title("🌿 CuidaFácil")
    st.caption("Cuidados simples. Constância real.")
    st.caption("Navegue por módulos para acompanhar sua rotina com clareza.")
    st.divider()

    if "user" not in st.session_state:
        st.markdown("### Acesso")

        tipo_acesso = st.radio(
            "Como deseja acessar?",
            ["Já tenho cadastro", "Quero me cadastrar"],
            index=0,
        )

        if tipo_acesso == "Já tenho cadastro":
            with st.form("login_existente_form"):
                email_login = st.text_input(
                    "E-mail cadastrado",
                    placeholder="seuemail@exemplo.com",
                    max_chars=120,
                )
                entrar = st.form_submit_button("Entrar")

            if entrar:
                email_limpo = email_login.strip().lower()

                if not is_valid_email(email_limpo):
                    st.warning("Informe um e-mail válido.")
                else:
                    with st.spinner("Entrando..."):
                        user = login_existing_user(email_limpo)

                    if user is None:
                        st.error(
                            "Não encontrei cadastro com esse e-mail. "
                            "Selecione 'Quero me cadastrar' para criar sua conta."
                        )
                    else:
                        st.session_state["user"] = user
                        st.session_state["nome"] = user.get("nome", "")
                        st.session_state["email"] = user.get("email", email_limpo)
                        st.session_state["session_recorded"] = False
                        st.session_state["page"] = "🏠 Início"
                        st.session_state["login_message"] = (
                            f"Bem-vindo de volta, {user.get('nome', '')}!"
                        )
                        st.rerun()

        else:
            with st.form("novo_cadastro_form"):
                primeiro_nome = st.text_input(
                    "Primeiro nome",
                    placeholder="Ex: Silvia",
                    max_chars=40,
                )
                email_cadastro = st.text_input(
                    "E-mail",
                    placeholder="seuemail@exemplo.com",
                    max_chars=120,
                )
                cadastrar = st.form_submit_button("Cadastrar")

            if cadastrar:
                primeiro_nome_limpo = primeiro_nome.strip()
                email_limpo = email_cadastro.strip().lower()

                if not primeiro_nome_limpo:
                    st.warning("Informe seu primeiro nome.")
                elif len(primeiro_nome_limpo.split()) > 1:
                    st.warning("Informe apenas o primeiro nome.")
                elif not is_valid_email(email_limpo):
                    st.warning("Informe um e-mail válido.")
                elif find_user_by_email(email_limpo) is not None:
                    st.error(
                        "Já existe cadastro com esse e-mail. "
                        "Selecione 'Já tenho cadastro' para entrar."
                    )
                else:
                    with st.spinner("Criando cadastro..."):
                        user = register_new_user(
                            primeiro_nome=primeiro_nome_limpo,
                            email=email_limpo,
                        )

                    st.session_state["user"] = user
                    st.session_state["nome"] = user.get("nome", primeiro_nome_limpo)
                    st.session_state["email"] = user.get("email", email_limpo)
                    st.session_state["session_recorded"] = False
                    st.session_state["page"] = "🏠 Início"
                    st.session_state["login_message"] = (
                        "Cadastro criado com sucesso. Bem-vindo ao CuidaFácil!"
                    )
                    st.rerun()

    else:
        user = st.session_state["user"]
        st.success(f"Logado como {user.get('nome', '')}")
        st.caption(user.get("email", ""))

        is_admin_sidebar = user.get("email", "").strip().lower() == admin_email()
        page_options = ["🏠 Início", "📊 Meu progresso", "🪴 Cuidador IA de Plantas", "⚙️ Configuração inicial"]
        if is_admin_sidebar:
            page_options.insert(2, "🧪 Admin")

        current_page = st.session_state.get("page", "🏠 Início")
        if current_page not in page_options:
            current_page = "🏠 Início"

        st.session_state["page"] = st.radio(
            "Navegação",
            page_options,
            index=page_options.index(current_page),
        )

        if st.button("Sair"):
            for key in ["user", "session_recorded", "login_message", "page"]:
                st.session_state.pop(key, None)
            st.rerun()

hero("CuidaFácil", "Um app simples para transformar pequenas atividades em hábitos.")
quote_card(st.session_state["proverbio"])

if st.session_state.get("login_message"):
    st.success(st.session_state.pop("login_message"))

if "user" not in st.session_state:
    page = st.radio(
        "Antes de começar",
        ["Landing", "Entrar", "Configuração inicial"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if page == "Landing":
        render_landing()
    elif page == "Entrar":
        st.info(
            "Escolha na lateral se você já tem cadastro ou se deseja criar uma conta. "
            "Para entrar, usamos apenas seu e-mail."
        )
    else:
        render_setup()

    st.stop()

user = st.session_state["user"]
record_session_once(user)

page = st.session_state.get("page", "🏠 Início")
is_admin = user.get("email", "").strip().lower() == admin_email()

if page == "🏠 Início":
    render_home(user)
elif page == "📊 Meu progresso":
    render_progress(user)
elif page == "🪴 Cuidador IA de Plantas":
    render_plant_ai(user)
elif page == "🧪 Admin" and is_admin:
    render_admin(user)
else:
    render_setup()
