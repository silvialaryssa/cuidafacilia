from __future__ import annotations

import streamlit as st

from services.app_service import user_progress_summary
from ui.components import metric_card


def render_progress(user: dict) -> None:
    st.subheader("Meu progresso")
    st.write("O progresso agora considera apenas as atividades previstas pela agenda.")

    summary = user_progress_summary(user)

    st.markdown("### Hoje")
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Previstas", str(summary["hoje"]["previstas"]))
    with c2:
        metric_card("Concluídas", str(summary["hoje"]["concluidas"]))
    with c3:
        metric_card("Progresso", f'{summary["hoje"]["progresso"]}%')

    st.divider()

    st.markdown("### Semana")
    c4, c5, c6 = st.columns(3)
    with c4:
        metric_card("Previstas", str(summary["semana"]["previstas"]))
    with c5:
        metric_card("Concluídas", str(summary["semana"]["concluidas"]))
    with c6:
        metric_card("Índice de Consistência", f'{summary["semana"]["progresso"]}%')

    st.divider()

    st.markdown("### Mês")
    c7, c8, c9 = st.columns(3)
    with c7:
        metric_card("Previstas", str(summary["mes"]["previstas"]))
    with c8:
        metric_card("Concluídas", str(summary["mes"]["concluidas"]))
    with c9:
        metric_card("Índice mensal", f'{summary["mes"]["progresso"]}%')
