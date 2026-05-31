from __future__ import annotations

import streamlit as st

from ui.category_selector import CATEGORIAS


def render_activity_card(row, on_complete, on_uncomplete, on_cancel, completed: bool = False) -> None:
    categoria = str(row.get("categoria", "Outro"))
    icone = CATEGORIAS.get(categoria, "⋯")
    titulo = str(row.get("titulo", categoria))
    horario = str(row.get("horario", ""))
    frequencia = str(row.get("frequencia", ""))
    descricao = str(row.get("descricao", ""))
    id_atividade = str(row.get("id_atividade", ""))

    card_class = "activity-paper-card done" if completed else "activity-paper-card pending"
    title_class = "activity-title done" if completed else "activity-title"
    desc_class = "activity-desc done" if completed else "activity-desc"

    with st.container():
        col_check, col_content, col_cancel = st.columns([0.75, 6.3, 0.85])

        with col_check:
            if completed:
                if st.button("✓", key=f"uncomplete_{id_atividade}", use_container_width=True, help="Desmarcar atividade"):
                    on_uncomplete(row)
            else:
                if st.button("✓", key=f"complete_{id_atividade}", use_container_width=True, help="Marcar como realizada"):
                    on_complete(row)

        with col_content:
            st.markdown(
                f'''<div class="{card_class}">
                    <div class="activity-paper-line"></div>
                    <div class="activity-card-header">
                        <span class="activity-card-icon">{icone}</span>
                        <span class="{title_class}">{titulo}</span>
                    </div>
                    <div class="activity-meta">{horario} • {frequencia}</div>
                    <div class="{desc_class}">{descricao}</div>
                </div>''',
                unsafe_allow_html=True,
            )

        with col_cancel:
            if st.button("×", key=f"cancel_{id_atividade}", use_container_width=True, help="Cancelar agendamento"):
                on_cancel(row)
