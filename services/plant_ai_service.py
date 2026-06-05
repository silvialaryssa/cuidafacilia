from __future__ import annotations

from dataclasses import dataclass

import requests
import streamlit as st

from config.settings import (
    chatgpt_api_base_url,
    chatgpt_api_key,
    gemini_api_base_url,
    gemini_api_key,
)
from services.app_service import get_ai_settings


@dataclass
class PlantAiRequest:
    funcionalidade: str
    planta: str
    ambiente: str
    sintomas: str
    contexto: str = ""


def _build_prompt(payload: PlantAiRequest) -> str:
    return (
        "Você é um assistente de jardinagem doméstica focado em respostas práticas, "
        "simples e seguras para iniciantes. "
        "Sempre responda em português do Brasil com este formato:\n"
        "1) Diagnóstico provável\n"
        "2) Ação imediata (próximas 24h)\n"
        "3) Plano de 7 dias\n"
        "4) Sinais de melhora e de alerta\n"
        "5) Erros comuns para evitar\n\n"
        f"Funcionalidade escolhida: {payload.funcionalidade}\n"
        f"Tipo de planta: {payload.planta}\n"
        f"Ambiente: {payload.ambiente}\n"
        f"Sintomas/objetivo: {payload.sintomas}\n"
        f"Contexto adicional: {payload.contexto or 'Não informado'}"
    )


def _extract_openai_text(data: dict) -> str:
    output = data.get("output", [])
    texts: list[str] = []

    for item in output:
        if item.get("type") != "message":
            continue

        for content in item.get("content", []):
            if content.get("type") == "output_text":
                value = str(content.get("text", "")).strip()
                if value:
                    texts.append(value)

    if texts:
        return "\n\n".join(texts).strip()

    # Fallback para formatos diferentes.
    try:
        return str(data["choices"][0]["message"]["content"]).strip()
    except Exception:
        return ""


def _extract_gemini_text(data: dict) -> str:
    texts: list[str] = []

    for candidate in data.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            value = str(part.get("text", "")).strip()
            if value:
                texts.append(value)

    return "\n\n".join(texts).strip()


class PlantAiService:
    def __init__(self) -> None:
        settings = get_ai_settings()
        self.provider = settings["provider"]
        self.model = settings["model"]

    def ask_for_guidance(self, payload: PlantAiRequest) -> str:
        prompt = _build_prompt(payload)

        if self.provider == "openai":
            return self._ask_openai(prompt)

        if self.provider == "gemini":
            return self._ask_gemini(prompt)

        raise RuntimeError(f"Provedor de IA não suportado: {self.provider}")

    def _ask_openai(self, prompt: str) -> str:
        api_key = chatgpt_api_key()
        base_url = chatgpt_api_base_url()

        if not api_key:
            raise RuntimeError("API key da OpenAI/ChatGPT não configurada.")

        response = requests.post(
            f"{base_url}/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": prompt,
            },
            timeout=45,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Erro ao chamar OpenAI ({response.status_code}): {response.text[:300]}"
            )

        text = _extract_openai_text(response.json())
        if not text:
            raise RuntimeError("A OpenAI não retornou texto útil.")

        return text

    def _ask_gemini(self, prompt: str) -> str:
        api_key = gemini_api_key()
        base_url = gemini_api_base_url()

        if not api_key:
            raise RuntimeError("API key do Google Gemini não configurada.")

        url = f"{base_url}/models/{self.model}:generateContent"

        response = requests.post(
            url,
            params={"key": api_key},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.5,
                    "maxOutputTokens":2048,
                },
            },
            timeout=60,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Erro ao chamar Gemini ({response.status_code}): {response.text[:300]}"
            )

        text = _extract_gemini_text(response.json())
        if not text:
            raise RuntimeError("O Gemini não retornou texto útil.")

        return text


def get_plant_ai_service() -> PlantAiService:
    # Não usar cache aqui, porque o Admin pode mudar o provedor/modelo durante a sessão.
    return PlantAiService()
