import os
import json
import click
from rich.console import Console
from rich.prompt import Prompt
import subprocess

console = Console()
CONFIG_FILE = "cv-workspace/resumecraftr.json"
LATEX_TEMPLATE = "cv-workspace/resume_template.tex"


@click.command()
def generate_pdf():
    """Generate a PDF resume using the optimized LaTeX template."""
    # Load configuration
    if not os.path.exists(CONFIG_FILE):
        console.print(
            "[bold red]Configuration file not found. Run 'resumecraftr init' first.[/bold red]"
        )
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    extracted_files = config.get("extracted_files", [])

    if not extracted_files:
        console.print(
            "[bold red]No extracted CV sections found in configuration.[/bold red]"
        )
        return

    extracted_files = [
        f.replace(".txt", ".optimized_sections.json") for f in extracted_files
    ]
    sections_file = extracted_files[0]

    if len(extracted_files) > 1:
        sections_file = Prompt.ask(
            "Multiple optimized CV files detected. Choose one", choices=extracted_files
        )

    sections_path = os.path.abspath(os.path.join("cv-workspace", sections_file))

    if not os.path.exists(sections_path):
        console.print(
            f"[bold red]Selected optimized sections file '{sections_file}' does not exist.[/bold red]"
        )
        return

    console.print(f"[bold blue]Generating PDF using: {sections_file}[/bold blue]")

    with open(sections_path, "r", encoding="utf-8") as f:
        sections_content = json.load(f)

    # Load LaTeX template
    if not os.path.exists(LATEX_TEMPLATE):
        console.print(
            f"[bold red]LaTeX template '{LATEX_TEMPLATE}' not found.[/bold red]"
        )
        return

    with open(LATEX_TEMPLATE, "r", encoding="utf-8") as f:
        latex_template = f.read()

    # Replace placeholders with actual content
    for section, content in sections_content.items():
        placeholder = f"{{{{{section}}}}}"  # LaTeX placeholders like {{Summary}}
        latex_template = latex_template.replace(placeholder, content)

    # Save to .tex file
    output_tex_file = os.path.join(
        "cv-workspace", sections_file.replace(".optimized_sections.json", ".tex")
    )
    output_pdf_file = output_tex_file.replace(".tex", ".pdf")

    with open(output_tex_file, "w", encoding="utf-8") as f:
        f.write(latex_template)

    console.print(f"[bold cyan]Compiling LaTeX file: {output_tex_file}[/bold cyan]")

    # Compile LaTeX to PDF
    try:
        subprocess.run(
            ["xelatex", "-output-directory=cv-workspace", output_tex_file], check=True
        )
        console.print(
            f"[bold green]PDF successfully generated: {output_pdf_file}[/bold green]"
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error during LaTeX compilation: {e}[bold red]")
        return


if __name__ == "__main__":
    generate_pdf()
