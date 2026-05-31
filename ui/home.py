from __future__ import annotations

from datetime import date, time

import streamlit as st

from services.app_service import (
    cancel_activity,
    complete_activity,
    create_activity,
    uncomplete_activity,
    user_executions_for_date,
    user_scheduled_activities,
)
from ui.activity_cards import render_activity_card
from ui.category_selector import CATEGORIAS, render_category_selector
from ui.dashboard_cards import render_summary_cards


FREQUENCIAS = ["Diária", "Semanal", "Uma vez"]
DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def _time_to_str(value) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")
    return str(value)


def _default_description(categoria: str) -> str:
    exemplos = {
        "Água": "Beber 2 copos de água pela manhã",
        "Saúde": "Tomar remédio ou cuidar da saúde",
        "Planta": "Regar as plantas",
        "Pet": "Dar comida ao pet",
        "Exercício": "Caminhar por 20 minutos",
        "Estudo": "Estudar por 30 minutos",
        "Feira": "Comprar frutas e verduras",
        "Casa": "Organizar um cômodo da casa",
        "Outro": "Descreva sua atividade",
    }
    return exemplos.get(categoria, "Descreva sua atividade")


def render_home(user: dict) -> None:
    hoje = date.today()

    st.subheader(f"Olá, {user.get('nome', 'usuário')} 👋")
    st.write("Aqui aparecem apenas as atividades previstas para hoje, de acordo com sua agenda.")

    if st.session_state.get("save_message"):
        st.success(st.session_state.pop("save_message"))

    activities = user_scheduled_activities(user, hoje)
    executions = user_executions_for_date(user, hoje)

    completed_ids = set()
    if not executions.empty and "id_atividade" in executions.columns:
        completed_ids = set(executions["id_atividade"].astype(str))

    total = len(activities)
    concluidas = len(completed_ids)
    pendentes = max(total - concluidas, 0)
    progresso = (concluidas / total * 100) if total else 0

    main_col, side_col = st.columns([2.2, 1], gap="large")

    with main_col:
        with st.expander("➕ Criar novo agendamento", expanded=total == 0):
            st.markdown('<div class="new-activity-panel">', unsafe_allow_html=True)

            categoria = render_category_selector()

            st.divider()
            st.markdown("### 2. Detalhes da agenda")

            st.markdown("### 3. Agenda")

            data_inicio = st.date_input(
                "Data de início",
                value=hoje,
                key="data_inicio_agendamento",
            )

            frequencia = st.radio(
                "Frequência",
                FREQUENCIAS,
                horizontal=True,
                key="frequencia_agendamento",
            )

            dias_semana = ""
            data_fim = ""

            if frequencia == "Semanal":
                st.markdown("#### Qual dia da semana?")

                dia_semana = st.radio(
                    "Dia da semana",
                    DIAS_SEMANA,
                    horizontal=True,
                    index=data_inicio.weekday(),
                    label_visibility="collapsed",
                    key="dia_semana_agendamento",
                )

                dias_semana = dia_semana

            elif frequencia == "Diária":
                st.markdown(
                    """
                    <div class="frequency-hint">
                        <span>✓</span>
                        <strong>Todos os dias</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            elif frequencia == "Uma vez":
                st.markdown(
                    """
                    <div class="frequency-hint">
                        <span>✓</span>
                        <strong>Apenas uma vez na data escolhida</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.divider()
            st.markdown("### 4. Descrição e horário")

            with st.form("form_atividade", clear_on_submit=True):
                descricao = st.text_area(
                    "Descrição",
                    placeholder=f"Ex: {_default_description(categoria)}",
                    height=90,
                )

                horario = st.time_input(
                    "Horário",
                    value=time(8, 0),
                    step=300,
                )

                st.markdown(
                    """<div class="tip-card">
                        <span class="tip-icon">🌱</span>
                        <span><strong>Dica:</strong> sua atividade aparecerá apenas nos dias previstos pela agenda.</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

                submitted = st.form_submit_button(
                    "💾 Salvar agendamento",
                    use_container_width=True,
                )

                if submitted:
                    if frequencia == "Semanal" and not dias_semana:
                        st.warning("Escolha um dia da semana.")
                    else:
                        titulo = categoria
                        descricao_final = descricao.strip() or _default_description(categoria)

                        try:
                            create_activity(
                                user=user,
                                titulo=titulo,
                                categoria=categoria,
                                descricao=descricao_final,
                                frequencia=frequencia,
                                horario=_time_to_str(horario),
                                data_inicio=data_inicio.isoformat(),
                                data_fim=data_fim,
                                dias_semana=dias_semana,
                            )

                            if data_inicio == hoje:
                                st.session_state["save_message"] = "Agendamento salvo com sucesso."
                            else:
                                st.session_state["save_message"] = (
                                    f"Agendamento salvo. Ele aparecerá a partir de {data_inicio.strftime('%d/%m/%Y')}."
                                )

                            st.rerun()

                        except Exception as erro:
                            st.error(f"Não foi possível salvar o agendamento: {erro}")

            st.markdown("</div>", unsafe_allow_html=True)

        st.subheader("Atividades de hoje")
        st.caption(hoje.strftime("%d/%m/%Y"))

        if activities.empty:
            st.info("Você não tem atividades previstas para hoje. Crie um novo agendamento acima.")
            return

        def concluir(row):
            id_atividade = str(row.get("id_atividade", ""))
            if id_atividade in completed_ids:
                return
            complete_activity(user, id_atividade, row.get("titulo", ""), data_referencia=hoje.isoformat())
            st.rerun()

        def desmarcar(row):
            id_atividade = str(row.get("id_atividade", ""))
            if id_atividade not in completed_ids:
                return
            uncomplete_activity(user, id_atividade, row.get("titulo", ""), data_referencia=hoje.isoformat())
            st.rerun()

        def cancelar(row):
            cancel_activity(user, row.get("id_atividade", ""), row.get("titulo", ""))
            st.rerun()

        for _, row in activities.iterrows():
            completed = str(row.get("id_atividade", "")) in completed_ids
            render_activity_card(row, concluir, desmarcar, cancelar, completed=completed)

    with side_col:
        render_summary_cards(total, concluidas, pendentes, progresso)

        st.markdown("### Categorias de hoje")
        if activities.empty:
            st.caption("As categorias aparecerão aqui quando houver agenda para hoje.")
        else:
            counts = activities.groupby("categoria").size().sort_values(ascending=False)
            for categoria, qtd in counts.items():
                icone = CATEGORIAS.get(str(categoria), "⋯")
                st.markdown(
                    f'''<div class="category-row">
                        <span>{icone} {categoria}</span>
                        <strong>{qtd}</strong>
                    </div>''',
                    unsafe_allow_html=True,
                )
