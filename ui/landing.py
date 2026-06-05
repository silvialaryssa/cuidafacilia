from __future__ import annotations

import streamlit as st

from ui.components import figure_card


BENEFICIOS = [
    ("✅", "Rotina simplificada", "Crie agendamentos em poucos cliques e mantenha consistência diária."),
    ("📊", "Progresso visual", "Acompanhe indicadores de hoje, semana e mês com clareza."),
    ("🪴", "Cuidador IA", "Receba orientações práticas para cuidados com plantas."),
    ("☁️", "Dados em nuvem", "Integração com Google Sheets e métricas com GA4."),
]


def render_landing() -> None:
    st.subheader("CuidaFácil: constância sem complicação")
    st.markdown(
        """
        <div class="section-intro">
            Um aplicativo leve para transformar pequenas ações em hábitos consistentes,
            com interface intuitiva e experiência responsiva em qualquer dispositivo.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1.35, 1], gap="large")

    with col_left:
        st.markdown(
            """
            <div class="landing-highlight">
                <h3>Comece em 3 passos</h3>
                <ol>
                    <li>Crie sua conta com e-mail.</li>
                    <li>Defina atividades e frequência.</li>
                    <li>Acompanhe progresso e mantenha o foco.</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

        feat_1, feat_2 = st.columns(2)
        with feat_1:
            figure_card("💧", "Hábitos diários", "Organize cuidados com saúde, água, casa, estudo e mais.")
        with feat_2:
            figure_card("📅", "Agenda inteligente", "Atividades aparecem somente nos dias previstos.")

        st.markdown(
            """
            <div class="landing-cta">
                <strong>Pronto para começar?</strong>
                <span>Use a aba Entrar para acessar sua conta ou fazer cadastro em segundos.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown(
            """
            <div class="landing-figure" aria-hidden="true">
                <div class="landing-figure-main">🌿</div>
                <div class="landing-figure-chip">Mobile + Desktop</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for icon, title, text in BENEFICIOS:
            figure_card(icon, title, text)
