import json
import os
from pathlib import Path

import click
from rich.console import Console
from rich.prompt import Prompt

from resumecraftr.cli.agent import create_or_get_agent

console = Console()
CONFIG_FILE = Path("cv-workspace/resumecraftr.json")
OUTPUT_FILE = Path("cv-workspace/{0}.tailored_sections.json")


@click.command()
def tailor_cv() -> None:
    """Tailor CV sections via a LangGraph RAG pipeline."""

    if not CONFIG_FILE.exists():
        console.print(
            "[bold red]Configuration file not found. Run 'resumecraftr setup' first.[/bold red]"
        )
        return

    with CONFIG_FILE.open("r", encoding="utf-8") as fh:
        config = json.load(fh)

    extracted_files = [
        fname.replace(".txt", ".extracted_sections.json")
        for fname in config.get("extracted_files", [])
    ]
    job_descriptions = config.get("job_descriptions", [])

    if not extracted_files or not job_descriptions:
        console.print(
            "[bold red]Missing parsed CV sections or job descriptions. Run 'import-cv', 'parse-cv' and 'add-job' first.[/bold red]"
        )
        return

    sections_file = extracted_files[0]
    job_desc_file = job_descriptions[0]

    if len(extracted_files) > 1:
        sections_file = Prompt.ask(
            "Multiple parsed CV files detected. Choose one", choices=extracted_files
        )

    if len(job_descriptions) > 1:
        job_desc_file = Prompt.ask(
            "Multiple job descriptions detected. Choose one", choices=job_descriptions
        )

    sections_path = Path("cv-workspace") / sections_file
    job_desc_path = Path("cv-workspace/job_descriptions") / job_desc_file

    if not sections_path.exists() or not job_desc_path.exists():
        console.print(
            "[bold red]Selected files are missing. Please re-run the previous steps.[/bold red]"
        )
        return

    with sections_path.open("r", encoding="utf-8") as fh:
        sections_content = json.load(fh)

    with job_desc_path.open("r", encoding="utf-8") as fh:
        job_description = fh.read().strip()

    runtime = create_or_get_agent()
    runtime.rebuild_vector_store()
    graph = runtime.tailor_graph()

    sections_payload = []
    for section_name, content in sections_content.items():
        if isinstance(content, str):
            normalized = content
        else:
            normalized = json.dumps(content, indent=2)
        sections_payload.append({"name": section_name, "content": normalized})

    if not sections_payload:
        console.print("[bold red]The selected sections file is empty.[/bold red]")
        return

    console.print(
        f"[bold blue]Running LangGraph tailoring for {len(sections_payload)} sections...[/bold blue]"
    )

    optimized = graph.run(
        sections=sections_payload,
        job_description=job_description,
        language=config.get("primary_language", "EN"),
    )

    output_path = OUTPUT_FILE.with_name(
        OUTPUT_FILE.name.format(
            sections_file.replace(".txt", "").replace(".extracted_sections.json", "")
        )
    )

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(optimized, fh, indent=4, ensure_ascii=False)

    console.print(f"[bold green]Tailored CV saved to: {output_path}[/bold green]")
