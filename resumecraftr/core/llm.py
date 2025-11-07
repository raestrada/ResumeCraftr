"""LangChain-powered LLM and embedding factories."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional, List

from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.chat_models.ollama import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from sentence_transformers import SentenceTransformer


Provider = Literal["openai", "openrouter", "ollama"]


@dataclass(frozen=True)
class LLMConfig:
    """Configuration used to instantiate LangChain chat models."""

    provider: Provider = "openrouter"
    model: str = "deepseek/deepseek-chat"
    temperature: float = 0.4
    max_tokens: int = 1024


@dataclass(frozen=True)
class EmbeddingConfig:
    """Configuration for embedding generation."""

    provider: Literal["huggingface", "openai", "ollama"] = "huggingface"
    model: str = "sentence-transformers/all-MiniLM-L6-v2"


def _read_openrouter_api_key() -> Optional[str]:
    key_file = Path.home() / ".resumecraftr" / "openrouter_api_key.txt"
    if key_file.exists():
        value = key_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    return os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")


class SentenceTransformerEmbeddings(Embeddings):
    """Minimal wrapper around sentence-transformers for LangChain."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()


def create_chat_model(config: LLMConfig) -> BaseChatModel:
    """Instantiate a LangChain chat model for the requested provider."""

    if config.provider == "openai":
        return ChatOpenAI(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    if config.provider == "openrouter":
        api_key = _read_openrouter_api_key()
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not configured. Set the env var or create ~/.resumecraftr/openrouter_api_key.txt"
            )
        return ChatOpenAI(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    if config.provider == "ollama":
        return ChatOllama(
            model=config.model,
            temperature=config.temperature,
            num_predict=config.max_tokens,
        )

    raise ValueError(f"Unsupported provider: {config.provider}")


@lru_cache(maxsize=4)
def create_embeddings(config: Optional[EmbeddingConfig] = None) -> Embeddings:
    """Return a cached embedding instance based on the embedding config."""

    config = config or EmbeddingConfig()
    if config.provider == "huggingface":
        return SentenceTransformerEmbeddings(model_name=config.model)

    if config.provider == "openai":
        return OpenAIEmbeddings(model=config.model)

    if config.provider == "ollama":
        return OllamaEmbeddings(model=config.model)

    raise ValueError(f"Unsupported embedding provider: {config.provider}")
