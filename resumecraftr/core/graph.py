"""LangGraph pipelines driving the ResumeCraftr workflows."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, TypedDict

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langgraph.graph import END, StateGraph

from resumecraftr.core.llm import LLMConfig, create_chat_model


class SectionPayload(TypedDict):
    name: str
    content: str


class TailorState(TypedDict):
    job_description: str
    language: str
    sections: List[SectionPayload]
    index: int
    optimized: Dict[str, Dict]
    context_chunks: List[str]


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

    def run(self, sections: List[SectionPayload], job_description: str, language: str) -> Dict[str, Dict]:
        state = {
            "sections": sections,
            "job_description": job_description,
            "language": language,
            "index": 0,
            "optimized": {},
            "context_chunks": [],
        }
        app = self.build().compile()
        result = app.invoke(state)
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
        payload = self.chain.invoke(
            {
                "language": state["language"],
                "section_name": section["name"],
                "section_content": section["content"],
                "context": context,
                "job_description": state["job_description"],
            }
        )
        optimized = dict(state["optimized"])
        optimized[section["name"]] = payload
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
