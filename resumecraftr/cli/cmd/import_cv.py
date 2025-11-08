import json
import os

import click
import fitz

from resumecraftr.cli.ui import console, create_progress, activity
CONFIG_FILE = "cv-workspace/resumecraftr.json"

@click.command()
@click.argument("pdf_path", type=click.Path(exists=True))
def import_cv(pdf_path):
    """
    Import a CV from a PDF file and save it in the workspace directory, updating the config file.

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

    console.rule("[bold blue]Import CV[/bold blue]")
    console.print(f"[bold]PDF:[/] {pdf_path}")

    with fitz.open(pdf_path) as document, open(
        output_filename, "w", encoding="utf-8"
    ) as text_file, create_progress() as progress:
        task = progress.add_task(
            "[cyan]Extracting pages", total=document.page_count
        )
        for page in document:
            text = page.get_text("text")
            if text:
                text_file.write(text.strip() + "\n")
            progress.advance(task)

    console.print(
        f"[bold green]CV imported and saved to:[/bold green] {output_filename}"
    )

    # Update resumecraftr.json
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

    extracted_files = config.get("extracted_files", [])
    extracted_files.append(os.path.basename(output_filename))
    config["extracted_files"] = list(set(extracted_files))  # Ensure unique values

    with activity("Updating workspace config"):
        with open(CONFIG_FILE, "w", encoding="utf-8") as config_file:
            json.dump(config, config_file, indent=4)

    console.print(
        f"[bold green]Updated {CONFIG_FILE} with imported file.[/bold green]"
    ) 
