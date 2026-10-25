"""Construcción centralizada de modelos de chat para los agentes."""

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from config.settings import (
    ANTHROPIC_API_KEY,
    HF_API_BASE_URL,
    HF_EXTRACTOR_MODEL,
    HF_MODEL_ROUTE,
    HF_PLANNER_MODEL,
    HF_TIMEOUT_SECONDS,
    HF_TOKEN,
    LLM_MODEL,
    LLM_PROVIDER,
    OPENAI_API_KEY,
)


def create_chat_model(purpose: str = "extractor", temperature: float = 0.0):
    """Crea un modelo OpenAI, Anthropic o compatible con Hugging Face Router."""
    if LLM_PROVIDER == "huggingface":
        model = HF_PLANNER_MODEL if purpose == "planner" else HF_EXTRACTOR_MODEL
        route = (HF_MODEL_ROUTE or "").strip()
        if route and not model.endswith(f":{route}"):
            model = f"{model}:{route}"
        return ChatOpenAI(
            model=model,
            api_key=HF_TOKEN,
            base_url=HF_API_BASE_URL,
            temperature=temperature,
            timeout=HF_TIMEOUT_SECONDS,
        )

    if LLM_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
        model = LLM_MODEL if "claude" in LLM_MODEL.lower() else "claude-3-5-sonnet-20241022"
        return ChatAnthropic(model=model, temperature=temperature)

    if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        return ChatOpenAI(model=LLM_MODEL, temperature=temperature)

    raise ValueError(f"No hay credenciales configuradas para LLM_PROVIDER={LLM_PROVIDER}.")
