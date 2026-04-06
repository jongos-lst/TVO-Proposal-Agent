from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # LLM Provider
    llm_provider: Literal["ollama", "openrouter", "openai"] = "openrouter"

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"

    # Server
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"

    model_config = {"env_file": [".env", "../.env"], "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
