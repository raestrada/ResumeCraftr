from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.prompt import Prompt

from resumecraftr.pdf.document import build_resume_document
from resumecraftr.pdf.html_renderer import HtmlPdfRenderer, get_available_templates

console = Console()
CONFIG_FILE = Path("cv-workspace/resumecraftr.json")


def _detect_sections() -> list[str]:
    workspace = Path("cv-workspace")
    candidates = sorted(
        [
            str(path.relative_to(workspace))
            for path in workspace.glob("*.tailored_sections.json")
        ]
    )
    if candidates:
        return candidates
    return sorted(
        [
            str(path.relative_to(workspace))
            for path in workspace.glob("*.optimized_sections.json")
        ]
    )


@click.command()
@click.option(
    "--sections",
    "sections_file",
    type=str,
    help="Relative path to the tailored sections JSON file inside cv-workspace",
)
@click.option("--output", type=click.Path(), help="Destination PDF path")
@click.option(
    "--template",
    "template_name",
    type=str,
    help="HTML template to use for PDF rendering",
)
def export_pdf(
    sections_file: str | None,
    output: str | None,
    template_name: str | None,
) -> None:
    """Render a resume PDF with PyMuPDF using tailored JSON sections."""

    if not CONFIG_FILE.exists():
        console.print("[bold red]Configuration file missing. Run 'resumecraftr setup'.[/bold red]")
        return

    with CONFIG_FILE.open("r", encoding="utf-8") as fh:
        config = json.load(fh)

    available = _detect_sections()
    if not available:
        console.print(
            "[bold red]No tailored sections found. Run 'resumecraftr tailor-cv' first.[/bold red]"
        )
        return

    if sections_file is None:
        if len(available) == 1:
            sections_file = available[0]
        else:
            sections_file = Prompt.ask("Select tailored sections", choices=available)

    sections_path = Path("cv-workspace") / sections_file
    if not sections_path.exists():
        console.print(f"[bold red]Sections file '{sections_file}' not found.[/bold red]")
        return

    with sections_path.open("r", encoding="utf-8") as fh:
        tailored_sections = json.load(fh)

    base_name = sections_path.stem.replace(".tailored_sections", "")
    extracted_path = sections_path.with_name(f"{base_name}.extracted_sections.json")
    if not extracted_path.exists():
        console.print(
            f"[bold red]Original sections file '{extracted_path.name}' not found. Re-run parsing first.[/bold red]"
        )
        return

    with extracted_path.open("r", encoding="utf-8") as fh:
        extracted_sections = json.load(fh)

    resume_document = build_resume_document(extracted_sections, tailored_sections)
    workspace_dir = Path("cv-workspace")
    templates = get_available_templates(workspace=workspace_dir)
    if not templates:
        console.print("[bold red]No resume templates found.[/bold red]")
        return

    if template_name is None:
        if len(templates) == 1:
            template_name = templates[0]
        else:
            template_name = Prompt.ask(
                "Select PDF template", choices=templates
            )
    elif template_name not in templates:
        console.print(
            f"[bold red]Template '{template_name}' not found. Available: {', '.join(templates)}[/bold red]"
        )
        return

    renderer = HtmlPdfRenderer(template_name=template_name, workspace=workspace_dir)
    output_dir = Path("cv-workspace/output")
    output_dir.mkdir(exist_ok=True)
    if output:
        output_path = Path(output)
    else:
        slug = sections_path.stem.replace(".tailored_sections", "")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        output_path = output_dir / f"resume-{slug}-{timestamp}.pdf"

    renderer.render(resume_document, output_path)
    console.print(f"[bold green]PDF generated at {output_path}[/bold green]")


if __name__ == "__main__":
    export_pdf()
