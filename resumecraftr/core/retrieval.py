"""Workspace-aware ChromaDB integration."""
from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class RetrievalConfig:
    persist_directory: Path
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_provider: str = "huggingface"
    chunk_size: int = 800
    chunk_overlap: int = 150


class WorkspaceVectorStore:
    """Builds and exposes a retriever backed by embedded ChromaDB."""

    def __init__(
        self,
        workspace_root: Path,
        config: RetrievalConfig,
        embeddings: Embeddings,
    ) -> None:
        self.workspace_root = workspace_root
        self.config = config
        self.embeddings = embeddings
        self._store: Chroma | None = None

    @property
    def persist_directory(self) -> str:
        return str(self.config.persist_directory)

    def _load_raw_documents(self) -> List[Document]:
        supported_suffixes = {".txt", ".md", ".json"}
        documents: List[Document] = []
        for path in self.workspace_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in supported_suffixes:
                continue
            try:
                text = path.read_text(encoding="utf-8").strip()
            except UnicodeDecodeError:
                continue
            if not text:
                continue
            if path.suffix.lower() == ".json":
                try:
                    json_content = json.loads(text)
                    text = json.dumps(json_content, indent=2)
                except json.JSONDecodeError:
                    pass
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": str(path.relative_to(self.workspace_root)),
                    },
                )
            )
        return documents

    def rebuild(self) -> None:
        docs = self._load_raw_documents()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        chunks = splitter.split_documents(docs)
        if self.config.persist_directory.exists():
            shutil.rmtree(self.persist_directory)
        os.makedirs(self.persist_directory, exist_ok=True)
        self._store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
        )

    def _ensure_store(self) -> None:
        if self._store is not None:
            return
        if self.config.persist_directory.exists():
            self._store = Chroma(
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory,
            )
        else:
            self.rebuild()

    def as_retriever(self):
        self._ensure_store()
        return self._store.as_retriever(search_kwargs={"k": 4})

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"WorkspaceVectorStore(persist_directory={self.persist_directory})"
