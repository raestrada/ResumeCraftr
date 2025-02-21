import click
import os
import json
import PyPDF2
from rich.console import Console
from rich.progress import Progress

console = Console()
CONFIG_FILE = "cv-workspace/resumecraftr.json"
LATEX_TEMPLATE = "cv-workspace/resume_template.tex"

@click.command()
@click.argument("pdf_path", type=click.Path(exists=True))
def extract_text(pdf_path):
    """
    Extract text from a PDF and save it in the workspace directory, updating the config file.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        None
    """
    workspace_dir = "cv-workspace"
    os.makedirs(workspace_dir, exist_ok=True)

    output_filename = os.path.join(
        workspace_dir, os.path.basename(pdf_path).replace(".pdf", ".txt")
    )

    console.print(f"[bold green]Extracting text from:[/bold green] {pdf_path}")

    with open(pdf_path, "rb") as pdf_file, open(
        output_filename, "w", encoding="utf-8"
    ) as text_file:
        reader = PyPDF2.PdfReader(pdf_file)

        with Progress() as progress:
            task = progress.add_task(
                "[cyan]Processing pages...", total=len(reader.pages)
            )

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_file.write(text + "\n")
                progress.update(task, advance=1)

    console.print(
        f"[bold green]Text extracted and saved to:[/bold green] {output_filename}"
    )

    # Update resumecraftr.json
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

    extracted_files = config.get("extracted_files", [])
    extracted_files.append(os.path.basename(output_filename))
    config["extracted_files"] = list(set(extracted_files))  # Ensure unique values

    with open(CONFIG_FILE, "w", encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=4)

    console.print(
        f"[bold green]Updated {CONFIG_FILE} with extracted file.[/bold green]"
    )
