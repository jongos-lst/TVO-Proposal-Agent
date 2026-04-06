from langchain_core.language_models import BaseChatModel
from app.config import settings


def get_llm(provider: str | None = None, streaming: bool = True, temperature: float = 0.3) -> BaseChatModel:
    """Factory for LLM instances. Supports ollama, openrouter, and openai."""
    provider = provider or settings.llm_provider

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            streaming=streaming,
            temperature=temperature,
        )
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.openrouter_model,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            streaming=streaming,
            temperature=temperature,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            streaming=streaming,
            temperature=temperature,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
