"""LangGraph pipelines driving the ResumeCraftr workflows."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, TypedDict

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langgraph.graph import END, StateGraph

from resumecraftr.core.llm import LLMConfig, create_chat_model


class SectionPayload(TypedDict):
    id: str
    name: str
    content: str
    schema: Optional[str]


class TailorState(TypedDict):
    job_description: str
    language: str
    sections: List[SectionPayload]
    index: int
    optimized: Dict[str, Dict]
    context_chunks: List[str]


DEFAULT_SCHEMA_HINT = (
    "Return a JSON object with keys 'summary' (string), 'highlights' (list of strings), "
    "and optional 'details' (string). Do not include any other keys."
)

SCHEMA_INSTRUCTIONS = {
    "experience_entry": (
        "Return a JSON object with the same keys as provided: "
        "'Job Title', 'Company', 'Dates of Employment', and 'Responsibilities' "
        "(list of bullet strings). Rewrite the content but do not remove or rename keys."
    ),
    "project_entry": (
        "Return a JSON object with the same keys as provided: "
        "'Project Name', 'Description', and 'Technologies Used' (list of strings)."
    ),
    "publication_entry": (
        "Return a JSON object with the keys 'Title' and 'Details'. "
        "Do not add other keys; rewrite the text to align with the job."
    ),
    "skills_map": (
        "Return a JSON object with the keys 'Programming Languages' (list of strings) "
        "and 'Tools and Technologies' (list of strings)."
    ),
}

@dataclass
class ResumeTailorGraph:
    config: LLMConfig
    retriever: BaseRetriever

    def __post_init__(self) -> None:
        self.llm = create_chat_model(self.config)
        self.parser = JsonOutputParser()
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You are a resume optimization expert. Respond with JSON containing the keys\n"
                        "'summary' (string), 'highlights' (list of strings) and optional 'details' (string)."
                    ),
                ),
                (
                    "human",
                    (
                        "Rewrite the CV section so it aligns with the job description while remaining honest.\n"
                        "Language: {language}\n"
                        "Section name: {section_name}\n"
                        "Schema instructions: {structure_hint}\n"
                        "Current content:\n{section_content}\n"
                        "Retrieved workspace context:\n{context}\n"
                        "Job description:\n{job_description}\n"
                        "{format_instructions}"
                    ),
                ),
            ]
        ).partial(format_instructions=self.parser.get_format_instructions())
        self.chain = self.prompt | self.llm | self.parser

    def build(self) -> StateGraph:
        graph = StateGraph(TailorState)
        graph.add_node("retrieve", self._retrieve_context)
        graph.add_node("optimize", self._optimize_section)
        graph.add_edge("retrieve", "optimize")
        graph.add_conditional_edges("optimize", self._route, {"continue": "retrieve", "end": END})
        graph.set_entry_point("retrieve")
        return graph

    def run(
        self,
        sections: List[SectionPayload],
        job_description: str,
        language: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Dict[str, Dict]:
        state = {
            "sections": sections,
            "job_description": job_description,
            "language": language,
            "index": 0,
            "optimized": {},
            "context_chunks": [],
        }
        app = self.build().compile()
        recursion_limit = max(75, len(sections) * 3 + 10)
        if progress_callback:
            current_state = dict(state)
            for event in app.stream(state, config={"recursion_limit": recursion_limit}):
                for node_name, node_state in event.items():
                    current_state = {**current_state, **node_state}
                    if node_name == "optimize":
                        completed = current_state.get("index", 0)
                        section_name = "Section"
                        if completed and completed - 1 < len(sections):
                            section_name = sections[completed - 1]["name"]
                        progress_callback(
                            completed,
                            len(sections),
                            section_name,
                        )
            return current_state["optimized"]

        result = app.invoke(state, config={"recursion_limit": recursion_limit})
        return result["optimized"]

    # Node implementations -------------------------------------------------

    def _retrieve_context(self, state: TailorState) -> TailorState:
        section = state["sections"][state["index"]]
        query = f"{section['name']}\n\n{section['content']}\n\nJob description:\n{state['job_description']}"
        docs = self.retriever.invoke(query)
        context_chunks = [doc.page_content for doc in docs]
        return {
            **state,
            "context_chunks": context_chunks,
        }

    def _optimize_section(self, state: TailorState) -> TailorState:
        section = state["sections"][state["index"]]
        context = "\n---\n".join(state.get("context_chunks", [])) or "No extra context found"
        schema_hint = SCHEMA_INSTRUCTIONS.get(section.get("schema"), DEFAULT_SCHEMA_HINT)
        payload = self.chain.invoke(
            {
                "language": state["language"],
                "section_name": section["name"],
                "section_content": section["content"],
                "context": context,
                "job_description": state["job_description"],
                "structure_hint": schema_hint,
            }
        )
        optimized = dict(state["optimized"])
        optimized[section["id"]] = payload
        return {
            **state,
            "optimized": optimized,
            "index": state["index"] + 1,
            "context_chunks": [],
        }

    def _route(self, state: TailorState) -> str:
        if state["index"] >= len(state["sections"]):
            return "end"
        return "continue"
