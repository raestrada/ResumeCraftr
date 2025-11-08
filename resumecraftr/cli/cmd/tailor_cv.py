import json
from collections import Counter
from pathlib import Path

import click
from rich.prompt import Prompt

from resumecraftr.cli.agent import create_or_get_agent
from resumecraftr.cli.ui import console, activity, create_progress
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

    console.rule("[bold blue]Tailor CV[/bold blue]")
    with activity("Preparing LangChain runtime"):
        runtime = create_or_get_agent()
        runtime.rebuild_vector_store()
        graph = runtime.tailor_graph()

    structured_config = {
        "Work Experience": {"type": "list", "schema": "experience_entry"},
        "Projects": {"type": "list", "schema": "project_entry"},
        "Technical Skills": {"type": "map", "schema": "skills_map"},
        "Publications & Open Source Contributions": {
            "type": "list",
            "schema": "publication_entry",
        },
    }

    sections_payload = []
    payload_records = []
    payload_counter = 0

    def next_id(section: str) -> str:
        nonlocal payload_counter
        payload_counter += 1
        slug = section.replace(" ", "_").lower()
        return f"{slug}__{payload_counter}"

    for section_name, content in sections_content.items():
        section_cfg = structured_config.get(section_name)
        if section_cfg and section_cfg["type"] == "list" and isinstance(content, list):
            for idx, entry in enumerate(content):
                payload_id = next_id(section_name)
                sections_payload.append(
                    {
                        "id": payload_id,
                        "name": section_name,
                        "content": json.dumps(entry, indent=2),
                        "schema": section_cfg["schema"],
                    }
                )
                payload_records.append(
                    {
                        "id": payload_id,
                        "section_name": section_name,
                        "kind": "list",
                        "position": idx,
                    }
                )
        elif section_cfg and section_cfg["type"] == "map" and isinstance(content, dict):
            payload_id = next_id(section_name)
            sections_payload.append(
                {
                    "id": payload_id,
                    "name": section_name,
                    "content": json.dumps(content, indent=2),
                    "schema": section_cfg["schema"],
                }
            )
            payload_records.append(
                {
                    "id": payload_id,
                    "section_name": section_name,
                    "kind": "map",
                    "position": None,
                }
            )
        else:
            normalized = content if isinstance(content, str) else json.dumps(content, indent=2)
            payload_id = next_id(section_name)
            sections_payload.append(
                {
                    "id": payload_id,
                    "name": section_name,
                    "content": normalized,
                    "schema": None,
                }
            )
            payload_records.append(
                {
                    "id": payload_id,
                    "section_name": section_name,
                    "kind": "single",
                    "position": None,
                }
            )

    if not sections_payload:
        console.print("[bold red]The selected sections file is empty.[/bold red]")
        return

    total_sections = len(sections_payload)
    console.print(
        f"[bold blue]Running LangGraph tailoring for {total_sections} sections...[/bold blue]"
    )
    section_counts = Counter(record["section_name"] for record in payload_records)
    if section_counts:
        console.print("[bold]Section breakdown:[/bold]")
        for name, count in section_counts.items():
            console.print(f"  - {name}: {count}")

    with create_progress(transient=False) as progress:
        task_id = progress.add_task("[cyan]Optimizing sections", total=total_sections)

        def handle_progress(completed: int, _total: int, section_label: str) -> None:
            label = section_label or "Section"
            current = min(completed, total_sections)
            progress.update(
                task_id,
                completed=current,
                description=f"[cyan]{label} ({current}/{total_sections})",
            )

        optimized = graph.run(
            sections=sections_payload,
            job_description=job_description,
            language=config.get("primary_language", "EN"),
            progress_callback=handle_progress,
        )

    output_path = OUTPUT_FILE.with_name(
        OUTPUT_FILE.name.format(
            sections_file.replace(".txt", "").replace(".extracted_sections.json", "")
        )
    )

    assembled = {}
    list_buffers = {}

    for record in payload_records:
        payload = optimized.get(record["id"])
        if payload is None:
            continue
        kind = record["kind"]
        section_name = record["section_name"]
        if kind == "list":
            list_buffers.setdefault(section_name, []).append((record["position"], payload))
        elif kind == "map":
            assembled[section_name] = payload
        else:
            assembled[section_name] = payload

    for section_name, items in list_buffers.items():
        ordered = [value for _, value in sorted(items, key=lambda x: x[0])]
        assembled[section_name] = ordered

    for name, original in sections_content.items():
        assembled.setdefault(name, original)

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(assembled, fh, indent=4, ensure_ascii=False)

    console.print(f"[bold green]Tailored CV saved to: {output_path}[/bold green]")
