from __future__ import annotations

import re
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from repositories.sheets_repository import SheetsRepository
from services.analytics_service import get_analytics_service
from utils.dates import now_iso
from utils.ids import new_id


@st.cache_resource
def get_repo() -> SheetsRepository:
    return SheetsRepository()


def clear_data_cache() -> None:
    try:
        read_sheet_cached.clear()
        read_all_data_cached.clear()
    except Exception:
        pass


@st.cache_data(ttl=45, show_spinner=False)
def read_sheet_cached(sheet_name: str) -> pd.DataFrame:
    return get_repo().read(sheet_name)


@st.cache_data(ttl=45, show_spinner=False)
def read_all_data_cached() -> dict[str, pd.DataFrame]:
    repo = get_repo()
    return {
        "usuarios": repo.read("usuarios"),
        "atividades": repo.read("atividades"),
        "execucoes": repo.read("execucoes"),
        "sessoes": repo.read("sessoes"),
        "eventos_uso": repo.read("eventos_uso"),
    }


def repository_status() -> dict:
    return get_repo().status()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_first_name(nome: str) -> str:
    nome_limpo = " ".join(nome.strip().split())
    if not nome_limpo:
        return ""
    return nome_limpo.split()[0].capitalize()


def is_valid_email(email: str) -> bool:
    email_clean = normalize_email(email)
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.match(pattern, email_clean))


def find_user_by_email(email: str) -> dict | None:
    email_clean = normalize_email(email)
    users = read_sheet_cached("usuarios")
    if users.empty or "email" not in users.columns:
        return None

    found = users[users["email"].astype(str).str.lower().str.strip() == email_clean]
    if found.empty:
        return None
    return found.iloc[0].to_dict()


def login_existing_user(email: str) -> dict | None:
    repo = get_repo()
    analytics = get_analytics_service()
    email_clean = normalize_email(email)

    user = find_user_by_email(email_clean)
    if user is None:
        return None

    repo.update_user_last_access(str(user["id_usuario"]), now_iso())
    clear_data_cache()
    analytics.track("existing_user_login", email_clean, {"id_usuario": user.get("id_usuario", "")})
    return user


def register_new_user(primeiro_nome: str, email: str) -> dict | None:
    repo = get_repo()
    analytics = get_analytics_service()
    email_clean = normalize_email(email)
    nome_clean = normalize_first_name(primeiro_nome)

    if find_user_by_email(email_clean) is not None:
        return None

    user = {
        "id_usuario": new_id("U"),
        "nome": nome_clean,
        "email": email_clean,
        "data_cadastro": now_iso(),
        "ultimo_acesso": now_iso(),
        "ativo": "Sim",
    }
    repo.append("usuarios", user)
    clear_data_cache()
    analytics.track("user_registered", email_clean, {"nome": nome_clean})
    return user


def register_or_get_user(nome: str, email: str) -> dict:
    user = login_existing_user(email)
    if user is not None:
        return user

    new_user = register_new_user(nome, email)
    if new_user is None:
        raise ValueError("Não foi possível cadastrar o usuário.")
    return new_user


def record_session_once(user: dict) -> None:
    if st.session_state.get("session_recorded"):
        return

    repo = get_repo()
    analytics = get_analytics_service()
    repo.append("sessoes", {
        "id_sessao": new_id("S"),
        "id_usuario": user.get("id_usuario", ""),
        "data_hora_acesso": now_iso(),
    })
    clear_data_cache()
    analytics.track("app_opened", user.get("email", ""), {"id_usuario": user.get("id_usuario", "")})
    st.session_state["session_recorded"] = True


def log_event(user: dict, evento: str, detalhes: str = "") -> None:
    get_repo().append("eventos_uso", {
        "id_evento": new_id("EV"),
        "id_usuario": user.get("id_usuario", ""),
        "evento": evento,
        "data_hora": now_iso(),
        "detalhes": detalhes,
    })
    clear_data_cache()


def _to_date(value, default: date | None = None) -> date | None:
    if value is None or value == "":
        return default
    if isinstance(value, date):
        return value
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return default
        return parsed.date()
    except Exception:
        return default


def today_iso_date() -> str:
    return date.today().isoformat()


def weekday_name_br(target_date: date) -> str:
    nomes = {
        0: "Segunda",
        1: "Terça",
        2: "Quarta",
        3: "Quinta",
        4: "Sexta",
        5: "Sábado",
        6: "Domingo",
    }
    return nomes[target_date.weekday()]


def activity_occurs_on_date(activity: dict | pd.Series, target_date: date) -> bool:
    row = activity.to_dict() if hasattr(activity, "to_dict") else dict(activity)

    status = str(row.get("status", "Ativa")).strip()
    if not status:
        status = "Ativa"

    if status.lower() not in {"ativa", "ativo"}:
        return False

    data_inicio = _to_date(row.get("data_inicio"), _to_date(row.get("data_criacao"), target_date))
    data_fim = _to_date(row.get("data_fim"), None)

    if data_inicio and target_date < data_inicio:
        return False
    if data_fim and target_date > data_fim:
        return False

    frequencia = str(row.get("frequencia", "Diária")).strip()

    if frequencia == "Diária":
        return True

    if frequencia == "Semanal":
        dias_semana = str(row.get("dias_semana", "")).strip()

        if not dias_semana:
            return weekday_name_br(target_date) == weekday_name_br(data_inicio or target_date)

        dias = {d.strip() for d in dias_semana.split(",") if d.strip()}

        return weekday_name_br(target_date) in dias

    if frequencia == "Mensal":
        return bool(data_inicio and target_date.day == data_inicio.day)

    if frequencia == "Uma vez":
        return bool(data_inicio and target_date == data_inicio)

    return True


def create_activity(
    user: dict,
    titulo: str,
    categoria: str,
    descricao: str,
    frequencia: str,
    horario: str,
    data_inicio: str | None = None,
    data_fim: str | None = "",
    dias_semana: str | None = "",
) -> None:
    repo = get_repo()
    analytics = get_analytics_service()
    data_inicio_final = data_inicio or today_iso_date()

    sucesso = repo.append("atividades", {
        "id_atividade": new_id("A"),
        "id_usuario": user["id_usuario"],
        "titulo": titulo,
        "categoria": categoria,
        "descricao": descricao,
        "frequencia": frequencia,
        "horario": horario,
        "data_inicio": data_inicio_final,
        "data_fim": data_fim or "",
        "dias_semana": dias_semana or "",
        "data_criacao": now_iso(),
        "data_cancelamento": "",
        "data_exclusao": "",
        "status": "Ativa",
    })

    if not sucesso:
        raise RuntimeError(f"Erro ao salvar agendamento no Google Sheets: {repo.error_message}")

    log_event(user, "atividade_criada", f"{categoria}: {titulo}")
    analytics.track("activity_created", user.get("email", ""), {"categoria": categoria})
    clear_data_cache()


def complete_activity(user: dict, id_atividade: str, titulo: str = "", data_referencia: str | None = None) -> None:
    repo = get_repo()
    analytics = get_analytics_service()
    ref = data_referencia or today_iso_date()

    repo.append("execucoes", {
        "id_execucao": new_id("E"),
        "id_atividade": id_atividade,
        "id_usuario": user["id_usuario"],
        "data_referencia": ref,
        "data_hora_execucao": now_iso(),
    })
    log_event(user, "atividade_concluida", f"{ref} | {titulo}")
    analytics.track("activity_completed", user.get("email", ""), {"id_atividade": id_atividade})
    clear_data_cache()


def uncomplete_activity(user: dict, id_atividade: str, titulo: str = "", data_referencia: str | None = None) -> None:
    repo = get_repo()
    analytics = get_analytics_service()
    ref = data_referencia or today_iso_date()

    repo.delete_rows_where("execucoes", {
        "id_usuario": str(user["id_usuario"]),
        "id_atividade": str(id_atividade),
        "data_referencia": ref,
    })
    log_event(user, "atividade_desmarcada", f"{ref} | {titulo}")
    analytics.track("activity_uncompleted", user.get("email", ""), {"id_atividade": id_atividade})
    clear_data_cache()


def cancel_activity(user: dict, id_atividade: str, titulo: str = "") -> None:
    repo = get_repo()
    repo.update_row_values(
        "atividades",
        "id_atividade",
        str(id_atividade),
        {"status": "Cancelada", "data_cancelamento": now_iso()},
    )
    log_event(user, "atividade_cancelada", titulo)
    clear_data_cache()


def soft_delete_activity(user: dict, id_atividade: str, titulo: str = "") -> None:
    repo = get_repo()
    repo.update_row_values(
        "atividades",
        "id_atividade",
        str(id_atividade),
        {"status": "Excluída", "data_exclusao": now_iso()},
    )
    log_event(user, "atividade_excluida", titulo)
    clear_data_cache()


def user_activities(user: dict) -> pd.DataFrame:
    df = read_sheet_cached("atividades")
    if df.empty:
        return df
    return df[df["id_usuario"].astype(str) == str(user["id_usuario"])].copy()


def user_scheduled_activities(user: dict, target_date: date | None = None) -> pd.DataFrame:
    target_date = target_date or date.today()
    df = user_activities(user)
    if df.empty:
        return df
    mask = df.apply(lambda row: activity_occurs_on_date(row, target_date), axis=1)
    return df[mask].copy()


def user_executions(user: dict) -> pd.DataFrame:
    df = read_sheet_cached("execucoes")
    if df.empty:
        return df
    return df[df["id_usuario"].astype(str) == str(user["id_usuario"])].copy()


def user_executions_for_date(user: dict, target_date: date | None = None) -> pd.DataFrame:
    target_date = target_date or date.today()
    ref = target_date.isoformat()
    df = user_executions(user)

    if df.empty:
        return df

    if "data_referencia" not in df.columns:
        df["data_referencia"] = pd.to_datetime(
            df["data_hora_execucao"],
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

    df["data_referencia"] = pd.to_datetime(
        df["data_referencia"],
        errors="coerce",
    ).dt.strftime("%Y-%m-%d")

    return df[df["data_referencia"].astype(str) == ref].copy()


def user_home_data(user: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    target_date = date.today()
    return user_scheduled_activities(user, target_date), user_executions_for_date(user, target_date)


def planned_count_for_period(user: dict, start_date: date, end_date: date) -> int:
    activities = user_activities(user)
    if activities.empty:
        return 0

    total = 0
    current = start_date
    while current <= end_date:
        total += int(activities.apply(lambda row: activity_occurs_on_date(row, current), axis=1).sum())
        current += timedelta(days=1)
    return total


def completed_count_for_period(user: dict, start_date: date, end_date: date) -> int:
    execs = user_executions(user)

    if execs.empty:
        return 0

    if "data_referencia" not in execs.columns:
        execs["data_referencia"] = pd.to_datetime(
            execs["data_hora_execucao"],
            errors="coerce",
        )

    refs = pd.to_datetime(
        execs["data_referencia"],
        errors="coerce",
    )

    start_ts = pd.Timestamp(start_date).normalize()
    end_ts = pd.Timestamp(end_date).normalize()

    filtered = execs[
        (refs >= start_ts)
        & (refs <= end_ts)
    ]

    return int(
        filtered.drop_duplicates(
            subset=["id_atividade", "data_referencia"]
        ).shape[0]
    )


def user_progress_summary(user: dict) -> dict:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    month_start = today.replace(day=1)

    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    def block(start: date, end: date) -> dict:
        planned = planned_count_for_period(user, start, end)
        done = completed_count_for_period(user, start, end)
        progress = round((done / planned) * 100, 1) if planned else 0.0
        return {"previstas": planned, "concluidas": done, "progresso": progress}

    return {
        "hoje": block(today, today),
        "semana": block(week_start, week_end),
        "mes": block(month_start, month_end),
    }


def all_data() -> dict[str, pd.DataFrame]:
    return read_all_data_cached()
