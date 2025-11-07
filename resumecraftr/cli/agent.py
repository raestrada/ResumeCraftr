from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from rich.console import Console

from resumecraftr.core.graph import ResumeTailorGraph
from resumecraftr.core.llm import (
    EmbeddingConfig,
    LLMConfig,
    create_chat_model,
    create_embeddings,
)
from resumecraftr.core.retrieval import RetrievalConfig, WorkspaceVectorStore

load_dotenv()

WORKSPACE = Path("cv-workspace")
CONFIG_FILE = WORKSPACE / "resumecraftr.json"
console = Console()


def _load_config() -> Dict:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            "Configuration file not found. Run 'resumecraftr setup' first."
        )
    with CONFIG_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


class LangChainRuntime:
    _instance: "LangChainRuntime" | None = None

    def __init__(self) -> None:
        config = _load_config()
        llm_section = config.get("llm", {})
        retrieval_section = config.get("retrieval", {})
        self.llm_config = LLMConfig(**llm_section)
        self.embedding_config = EmbeddingConfig(
            provider=retrieval_section.get("embedding_provider", "huggingface"),
            model=retrieval_section.get(
                "embedding_model", "sentence-transformers/all-MiniLM-L6-v2"
            ),
        )
        self.llm = create_chat_model(self.llm_config)
        retrieval_config = RetrievalConfig(
            persist_directory=WORKSPACE
            / retrieval_section.get("persist_directory", ".chroma"),
            embedding_model=self.embedding_config.model,
            embedding_provider=self.embedding_config.provider,
            chunk_size=retrieval_section.get("chunk_size", 800),
            chunk_overlap=retrieval_section.get("chunk_overlap", 150),
        )
        embeddings = create_embeddings(self.embedding_config)
        self.vector_store = WorkspaceVectorStore(
            workspace_root=WORKSPACE,
            config=retrieval_config,
            embeddings=embeddings,
        )
        self._prompt_chain = (
            ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are ResumeCraftr, an expert technical writer."
                        " Provide actionable results and avoid prose unless requested.",
                    ),
                    ("human", "{input_text}"),
                ]
            )
            | self.llm
            | StrOutputParser()
        )

    @classmethod
    def instance(cls) -> "LangChainRuntime":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def run_prompt(self, prompt: str) -> str:
        return self._prompt_chain.invoke({"input_text": prompt})

    def rebuild_vector_store(self) -> None:
        self.vector_store.rebuild()

    def retriever(self):
        return self.vector_store.as_retriever()

    def tailor_graph(self) -> ResumeTailorGraph:
        return ResumeTailorGraph(config=self.llm_config, retriever=self.retriever())


def create_or_get_agent() -> LangChainRuntime:
    """Backwards compatible factory used by the CLI commands."""

    return LangChainRuntime.instance()


def execute_prompt(prompt: str, name: str | None = None) -> str:
    del name  # legacy compatibility
    runtime = create_or_get_agent()
    return runtime.run_prompt(prompt)
