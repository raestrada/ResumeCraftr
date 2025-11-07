import json
import os
from pathlib import Path

import click
from rich.console import Console

console = Console()

WORKSPACE = Path("cv-workspace")
CONFIG_FILE = WORKSPACE / "resumecraftr.json"
CUSTOM_FILE = WORKSPACE / "custom.md"


@click.command()
@click.option("--language", default="EN", show_default=True, help="Primary language for your resumes")
@click.option(
    "--provider",
    default="openrouter",
    type=click.Choice(["openai", "openrouter", "ollama"], case_sensitive=False),
    show_default=True,
    help="LLM provider to use through LangChain",
)
@click.option(
    "--model",
    default="deepseek/deepseek-chat",
    show_default=True,
    help="Model name that matches the selected provider",
)
@click.option("--temperature", default=0.4, show_default=True, help="Generation temperature")
def setup(language: str, provider: str, model: str, temperature: float) -> None:
    """Initialize a fully Python-native ResumeCraftr workspace."""

    WORKSPACE.mkdir(exist_ok=True)
    (WORKSPACE / "job_descriptions").mkdir(exist_ok=True)
    (WORKSPACE / "output").mkdir(exist_ok=True)
    (WORKSPACE / "templates" / "pdf").mkdir(parents=True, exist_ok=True)

    config = {
        "primary_language": language,
        "llm": {
            "provider": provider.lower(),
            "model": model,
            "temperature": temperature,
            "max_tokens": 1200,
        },
        "retrieval": {
            "persist_directory": ".chroma",
            "embedding_provider": "huggingface",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "chunk_size": 900,
            "chunk_overlap": 200,
        },
        "pdf": {
            "font": "helv",
            "heading_font_size": 14,
            "body_font_size": 11,
            "margin": 54,
        },
    }

    with CONFIG_FILE.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=4)

    if not CUSTOM_FILE.exists():
        CUSTOM_FILE.write_text("# Custom instructions\n", encoding="utf-8")

    _copy_default_template()

    console.print(f"[bold green]Workspace ready at {WORKSPACE.resolve()}[/bold green]")
    console.print("[bold green]Configuration saved with LangChain defaults.[/bold green]")


def _copy_default_template() -> None:
    from importlib import resources

    destination = WORKSPACE / "templates" / "pdf" / "modern.html"
    if destination.exists():
        return

    try:
        source = resources.files("resumecraftr.pdf.templates").joinpath("modern.html")
        data = source.read_text(encoding="utf-8")
        destination.write_text(data, encoding="utf-8")
        console.print(
            f"[bold green]Copied default template to {destination.relative_to(WORKSPACE)}[/bold green]"
        )
    except FileNotFoundError:
        console.print(
            "[bold yellow]Warning: could not find bundled modern.html template.[/bold yellow]"
        )
