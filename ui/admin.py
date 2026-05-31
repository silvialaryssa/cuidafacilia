from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from services.analytics_service import get_analytics_service
from services.app_service import all_data
from services.metrics_service import (
    calculate_admin_metrics,
    category_counts,
    completions_by_day,
    sessions_by_day,
)
from ui.components import metric_card


def render_admin(user: dict) -> None:
    if not st.session_state.get("admin_opened_tracked"):
        get_analytics_service().track("admin_opened", user.get("email", ""))
        st.session_state["admin_opened_tracked"] = True

    st.subheader("Admin • Métricas do Produto")

    data = all_data()
    metrics = calculate_admin_metrics(data)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Usuários", str(metrics["usuarios"]))
    with c2:
        metric_card("MAU", str(metrics["mau"]))
    with c3:
        metric_card("Retenção D7", f'{metrics["retencao_d7"]}%')
    with c4:
        metric_card("Ativação", f'{metrics["ativacao"]}%')

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        metric_card("Atividades", str(metrics["atividades"]))
    with c6:
        metric_card("Conclusões", str(metrics["execucoes"]))
    with c7:
        metric_card("Taxa conclusão", f'{metrics["conclusao"]}%')
    with c8:
        metric_card("DAU / WAU", f'{metrics["dau"]} / {metrics["wau"]}')

    st.divider()

    st.markdown("### Retenção")
    retention_df = pd.DataFrame({
        "Período": ["D1", "D7", "D30"],
        "Retenção (%)": [
            metrics["retencao_d1"],
            metrics["retencao_d7"],
            metrics["retencao_d30"],
        ],
    })
    fig_ret = px.bar(
        retention_df,
        x="Período",
        y="Retenção (%)",
        text="Retenção (%)",
        title="Retenção de usuários",
    )
    st.plotly_chart(fig_ret, use_container_width=True)

    st.markdown("### Funil de conversão")
    usuarios = metrics["usuarios"]
    ativados = data["atividades"]["id_usuario"].nunique() if not data["atividades"].empty else 0
    concluintes = data["execucoes"]["id_usuario"].nunique() if not data["execucoes"].empty else 0
    recorrentes = metrics["recorrentes"]

    funnel = pd.DataFrame({
        "Etapa": ["Cadastrou", "Criou atividade", "Concluiu atividade", "Voltou ao app"],
        "Usuários": [usuarios, ativados, concluintes, recorrentes],
    })

    fig_funnel = px.bar(
        funnel,
        x="Etapa",
        y="Usuários",
        text="Usuários",
        title="Funil do CuidaFácil",
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Categorias mais usadas")
        cat = category_counts(data["atividades"])
        if not cat.empty:
            fig = px.bar(cat, x="categoria", y="quantidade", text="quantidade")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Ainda não há categorias para exibir.")

    with col2:
        st.markdown("### Usuários ativos por dia")
        sess = sessions_by_day(data["sessoes"])
        if not sess.empty:
            fig2 = px.line(sess, x="data", y="usuarios_ativos", markers=True)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Ainda não há sessões para exibir.")

    st.markdown("### Conclusões por dia")
    daily_done = completions_by_day(data["execucoes"])
    if not daily_done.empty:
        fig3 = px.line(daily_done, x="data", y="conclusoes", markers=True)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Ainda não há conclusões para exibir.")

    with st.expander("Ver dados brutos"):
        for name, df in data.items():
            st.write(f"#### {name}")
            st.dataframe(df, use_container_width=True)
