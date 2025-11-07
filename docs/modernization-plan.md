# ResumeCraftr Modernization Plan

## Objectives
- Replace legacy OpenAI SDK usage with LangChain graph pipelines and native tooling only.
- Standardize LLM access through LangChain, targeting OpenRouter, OpenAI, and Ollama providers.
- Introduce embedded ChromaDB (SQLite backend) for all retrieval and vector storage.
- Generate PDFs exclusively with PyMuPDF to gain full control of layout and styling.
- Remove non-Python components, deprecated assets, and backward-compatibility shims.

## Phase 1 – Dependency & Environment Alignment
1. **Assess current stack**: inventory packages from `pyproject.toml`/`poetry.lock`, flag non-Python tooling, and identify legacy OpenAI SDK references.
2. **Define target runtime**: lock Python version (≥3.11) and document minimal OS prerequisites.
3. **Update dependencies**: add `langchain`, `langchain-core`, `langgraph`, `chromadb`, `PyMuPDF`, provider SDK shims (OpenAI, OpenRouter, Ollama clients), and remove obsolete libraries.
4. **CI adjustments**: update workflows/tests to install the new dependencies and drop steps tied to removed tooling.

## Phase 2 – LangChain Graph Architecture
1. **Use-case mapping**: document resume-generation scenarios (ingestion, enrichment, formatting) and break them into graph nodes.
2. **Graph design**: create LangChain graph pipelines that cover data ingestion, retrieval-augmented generation, validation, and PDF rendering requests.
3. **Interface layer**: expose graph entry points through a cohesive Python API/CLI, eliminating prior ad-hoc scripts.
4. **Observability**: integrate LangChain callbacks/logging for traces, token metrics, and error visibility.

## Phase 3 – Provider Abstraction via LangChain
1. **Provider selection module**: build a configuration-driven selector that instantiates LangChain LLMs for OpenRouter, OpenAI, or Ollama based on environment variables.
2. **Capability alignment**: ensure consistent model kwargs (temperature, max tokens) and retry policies across providers.
3. **Security**: centralize secret management (env vars or vault) and redact sensitive logs.

## Phase 4 – Embedded Retrieval with ChromaDB
1. **Data modeling**: define schema for resume snippets, templates, and user prompts; normalize metadata for filters.
2. **Embedding flow**: select embedding models compatible with LangChain and ChromaDB; implement batch ingestion jobs.
3. **SQLite backend tuning**: configure persistence directory, backup strategy, and integrity checks.
4. **RAG integration**: connect retrieval nodes in the LangChain graph to query ChromaDB collections before LLM calls.

## Phase 5 – PDF Generation with PyMuPDF
1. **Template system**: design theme definitions (colors, typography, spacing) in Python-native structures.
2. **Rendering engine**: implement PyMuPDF routines for layout composition, pagination, and asset embedding (icons, images).
3. **Style controls**: expose options for margins, columns, and inline highlights; ensure deterministic output for tests.
4. **Regression tests**: create snapshot-based PDF tests focusing on metadata, fonts, and layout integrity.

## Phase 6 – Legacy Cleanup
1. **Code removal**: delete unused OpenAI SDK wrappers, Node/JS helpers, and any non-Python automation.
2. **API refactors**: simplify public functions to align with the new LangChain-first workflow, accepting breaking changes as needed.
3. **Documentation refresh**: update README/docs with new setup, provider configuration, and troubleshooting tips.
4. **Migration guidance**: provide scripts or notes for users to re-ingest data into ChromaDB and switch configs.

## Phase 7 – Validation & Release
1. **Integration tests**: cover end-to-end flows (data ingestion → retrieval → LLM generation → PDF output).
2. **Performance benchmarks**: measure latency for each provider and retrieval operations; optimize chunking or caching.
3. **Release packaging**: cut a tagged release, publish updated docs, and communicate breaking changes.
4. **Post-release follow-up**: monitor issues, gather feedback, and prioritize refinements for future iterations.

## Deliverables & Success Criteria
- Updated dependency manifests free of legacy OpenAI SDK usage.
- LangChain graph pipelines committed with provider abstraction and ChromaDB-backed RAG.
- PyMuPDF rendering module producing customizable, testable PDF resumes.
- Documentation within `docs/` (and this `doca/` plan) reflecting the modernized architecture.
- Passing CI pipeline demonstrating end-to-end functionality without deprecated assets.
