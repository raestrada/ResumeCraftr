import os
import json
import shutil
import importlib.resources
import click
from rich.console import Console

console = Console()

CONFIG_FILE = os.path.join("cv-workspace", "resumecraftr.json")
CUSTOM_FILE = os.path.join("cv-workspace", "custom.md")

try:
    with importlib.resources.path(
        "resumecraftr.templates", "resume_template.md"
    ) as md_template_path:
        MD_TEMPLATE_SRC = str(md_template_path)
except ModuleNotFoundError:
    console.print(
        "[bold red]Error: Could not locate the template file inside the installed package.[/bold red]"
    )
    MD_TEMPLATE_SRC = None

MD_TEMPLATE_DEST = os.path.join("cv-workspace", "resume_template.md")

DEFAULT_CONFIG = {
    "primary_language": "EN",
    "output_format": "pdf",
    "template_name": "resume_template.md",
}

@click.command()
@click.option(
    "--language", default="EN", show_default=True, help="Language of the CV (EN or ES)"
)
@click.option(
    "--gpt-model", default="gpt-4o", show_default=True, help="chatGPT Model"
)
def setup(language, gpt_model):
    """Initialize a new ResumeCraftr workspace."""
    # Create workspace directory
    os.makedirs("cv-workspace", exist_ok=True)

    # Create or update config file
    config = DEFAULT_CONFIG.copy()
    config["primary_language"] = language
    config["chat_gpt"] = {
        "model": gpt_model,
        "temperature": 0.7,
        "top_p": 1.0,
    }

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    console.print(f"[bold green]Configuration file created:[/bold green] {CONFIG_FILE}")

    # Create custom.md if it doesn't exist
    if not os.path.exists(CUSTOM_FILE):
        with open(CUSTOM_FILE, "w", encoding="utf-8") as f:
            f.write("# Custom Instructions and Data\n\n")
        console.print(f"[bold green]Custom file created:[/bold green] {CUSTOM_FILE}")

    # Copy Markdown template if it doesn't exist
    if os.path.exists(MD_TEMPLATE_SRC) and not os.path.exists(MD_TEMPLATE_DEST):
        shutil.copy(MD_TEMPLATE_SRC, MD_TEMPLATE_DEST)
        console.print(f"[bold green]Markdown template copied to:[/bold green] {MD_TEMPLATE_DEST}")
    elif not os.path.exists(MD_TEMPLATE_SRC):
        console.print(
            f"[bold red]Markdown template source not found at:[/bold red] {MD_TEMPLATE_SRC}"
        )
    else:
        console.print(
            f"[bold yellow]Markdown template already exists in workspace:[/bold yellow] {MD_TEMPLATE_DEST}"
        )

    console.print("[bold green]Workspace initialized successfully![/bold green]") 