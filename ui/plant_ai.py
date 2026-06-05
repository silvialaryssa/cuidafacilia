from __future__ import annotations

from datetime import date, time

import streamlit as st

from config.settings import has_chatgpt_config, has_gemini_config
from services.app_service import create_activity
from services.plant_ai_service import PlantAiRequest, get_plant_ai_service
from ui.components import figure_card


FUNCIONALIDADES = [
    "Diagnóstico rápido (folhas amareladas/manchadas)",
    "Plano de rega personalizado",
    "Controle natural de pragas",
    "Recuperar planta murcha",
    "Planejamento semanal de cuidados",
]

AMBIENTES = [
    "Ambiente interno com pouca luz",
    "Ambiente interno com boa luz indireta",
    "Varanda / meia-sombra",
    "Ambiente externo com sol direto",
]

AGENDAMENTOS_RAPIDOS = [
    "Hoje (uma vez)",
    "Diária",
    "Semanal",
]

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def render_plant_ai(user: dict) -> None:
    hoje = date.today()

    st.subheader("Cuidador IA de Plantas")
    st.write(
        "Escolha uma funcionalidade, descreva sua planta e receba orientações práticas para os próximos dias."
    )
    st.markdown(
        """
        <div class="section-intro">
            Quanto mais contexto você informar, mais específica será a recomendação da IA.
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_help1, c_help2 = st.columns(2)
    with c_help1:
        figure_card("🪴", "Diagnóstico rápido", "Descreva folhas, caule e solo para resposta mais precisa.")
    with c_help2:
        figure_card("💧", "Plano de cuidado", "Receba frequência de rega e rotina semanal personalizada.")

    st.markdown("### 1) O que você precisa agora?")
    funcionalidade = st.radio(
        "Escolha a funcionalidade",
        FUNCIONALIDADES,
        horizontal=False,
        label_visibility="collapsed",
    )

    col1, col2 = st.columns(2)
    with col1:
        planta = st.text_input("Tipo de planta", placeholder="Ex: Jiboia, Rosa do deserto, Samambaia")
    with col2:
        ambiente = st.selectbox("Ambiente", AMBIENTES)

    sintomas = st.text_area(
        "Descreva sintomas ou objetivo",
        placeholder="Ex: Pontas secas e folhas caindo após mudança de local.",
        height=110,
    )
    contexto = st.text_input(
        "Contexto adicional (opcional)",
        placeholder="Ex: Moro em Brasília, clima seco, rego 2x por semana.",
    )

    if st.button("Gerar orientação com IA", use_container_width=True, type="primary"):
        if not planta.strip():
            st.warning("Informe o tipo da planta para uma recomendação melhor.")
            return
        if not sintomas.strip():
            st.warning("Descreva os sintomas ou objetivo para gerar o plano.")
            return
        if not (has_gemini_config() or has_chatgpt_config()):
            st.error(
                "Nenhuma API de IA configurada. Configure Gemini ou OpenAI em 'Configuração inicial'."
            )
            return

        with st.spinner("Consultando agente de plantas..."):
            try:
                response = get_plant_ai_service().ask_for_guidance(
                    PlantAiRequest(
                        funcionalidade=funcionalidade,
                        planta=planta.strip(),
                        ambiente=ambiente,
                        sintomas=sintomas.strip(),
                        contexto=contexto.strip(),
                    )
                )
            except Exception as err:
                st.error(f"Não foi possível gerar a orientação: {err}")
                return

        st.success(f"Plano gerado para {user.get('nome', 'você')}.")
        st.markdown("### Orientação do Cuidador IA")
        st.text_area(
            "Orientação do Cuidador IA",
             value=str(response),
            height=500,
            disabled=True
     )

        

   # with st.expander("Como obter respostas melhores"):
        #st.write("- Informe a espécie da planta, se souber.")
        #st.write("- Diga frequência de rega atual e incidência de luz.")
        #st.write("- Descreva há quanto tempo os sintomas começaram.")

    st.divider()
    st.markdown("### Agendar cuidado desta planta")
    st.caption("Crie um agendamento aqui e ele aparecerá em 'Atividades de hoje' quando for o dia previsto.")

    with st.form("plant_ai_schedule_form", clear_on_submit=False):
        plano = st.radio(
            "Plano de agendamento",
            AGENDAMENTOS_RAPIDOS,
            horizontal=True,
        )

        dia_semana = ""
        if plano == "Semanal":
            dia_semana = st.selectbox("Dia da semana", DIAS_SEMANA, index=hoje.weekday())

        col_ag1, col_ag2 = st.columns(2)
        with col_ag1:
            horario_agenda = st.time_input("Horário", value=time(8, 0), step=300)
        with col_ag2:
            data_inicio = st.date_input("Data de início", value=hoje)

        descricao_padrao = (
            f"{funcionalidade} para {planta.strip() or 'planta da casa'} em {ambiente.lower()}."
        )
        descricao_agenda = st.text_area(
            "Descrição do cuidado",
            value=descricao_padrao,
            height=90,
        )

        salvar_agendamento = st.form_submit_button("Salvar cuidado na agenda", use_container_width=True)

        if salvar_agendamento:
            if not descricao_agenda.strip():
                st.warning("Informe uma descrição para o cuidado da planta.")
            else:
                if plano == "Hoje (uma vez)":
                    frequencia = "Uma vez"
                    inicio = hoje
                    dias_semana = ""
                elif plano == "Diária":
                    frequencia = "Diária"
                    inicio = data_inicio
                    dias_semana = ""
                else:
                    frequencia = "Semanal"
                    inicio = data_inicio
                    dias_semana = dia_semana

                try:
                    create_activity(
                        user=user,
                        titulo="Planta",
                        categoria="Planta",
                        descricao=descricao_agenda.strip(),
                        frequencia=frequencia,
                        horario=horario_agenda.strftime("%H:%M"),
                        data_inicio=inicio.isoformat(),
                        data_fim="",
                        dias_semana=dias_semana,
                    )

                    st.session_state["save_message"] = "Cuidado com planta agendado com sucesso."
                    st.session_state["page"] = "🏠 Início"
                    st.success("Agendamento criado. Você será direcionado para Atividades de Hoje.")
                    st.rerun()
                except Exception as err:
                    st.error(f"Não foi possível salvar o agendamento: {err}")
