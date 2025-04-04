import click
import json
import os
import shutil
import importlib.resources
from rich.console import Console
from rich.progress import SpinnerColumn, TextColumn, Progress
from resumecraftr.cli.cmd.pdf import extract_text
from resumecraftr.cli.cmd.sections import extract_sections
from resumecraftr.cli.cmd.jobs_desc import add_job_description
from resumecraftr.cli.cmd.resume import optimize_resume
from resumecraftr.cli.cmd.latex import generate_pdf
from resumecraftr.cli.cmd.create_cv import create_cv, add_section, show_cv
from resumecraftr.cli.cmd.extract_pdf import extract_pdf
from resumecraftr.cli.cmd.tex_to_pdf import tex_to_pdf
from resumecraftr.cli.agent import delete_all_resumecraftr_agents

console = Console()

CONFIG_FILE = os.path.join("cv-workspace", "resumecraftr.json")
CUSTOM_FILE = os.path.join("cv-workspace", "custom.md")

try:
    with importlib.resources.path(
        "resumecraftr.templates", "resume_template.tex"
    ) as template_path:
        TEMPLATE_SRC = str(template_path)
except ModuleNotFoundError:
    console.print(
        "[bold red]Error: Could not locate the template file inside the installed package.[/bold red]"
    )
    TEMPLATE_SRC = None

TEMPLATE_DEST = os.path.join("cv-workspace", "resume_template.tex")

DEFAULT_CONFIG = {
    "primary_language": "EN",
    "output_format": "pdf",
    "template_name": "resume_template.tex",
}

@click.group()
def cli():
    """ResumeCraftr CLI tool"""
    pass

@click.command()
@click.option(
    "--language", default="EN", show_default=True, help="Language of the CV (EN or ES)"
)
@click.option(
    "--gpt-model", default="gpt-4o", show_default=True, help="chatGPT Model"
)
def init(language, gpt_model):
    """
    Initialize a new CV workspace with an optional language setting.

    :param language: Language of the CV (EN or ES)
    :param gpt_model: chatGPT Model
    """
    workspace_dir = "cv-workspace"
    os.makedirs(workspace_dir, exist_ok=True)

    # Validate language
    language = language.upper()
    if language not in ["EN", "ES"]:
        console.print(
            f"[bold red]Invalid language option:[/bold red] {language}. Use 'EN' or 'ES'."
        )
        return

    # Initial configuration
    config = DEFAULT_CONFIG.copy()
    config["primary_language"] = language
    config["chat_gpt"] = {
        "model": gpt_model
    }

    # Save configuration
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as config_file:
            json.dump(config, config_file, indent=4)
        console.print(
            f"[bold green]Workspace initialized with settings:[/bold green] {CONFIG_FILE}"
        )
    else:
        with open(CONFIG_FILE, "r+", encoding="utf-8") as config_file:
            existing_config = json.load(config_file)
            updated = False

            if (
                "primary_language" not in existing_config
                or existing_config["primary_language"] != language
            ):
                existing_config["primary_language"] = language
                updated = True

            if "template_name" not in existing_config:
                existing_config["template_name"] = DEFAULT_CONFIG["template_name"]
                updated = True

            if updated:
                config_file.seek(0)
                json.dump(existing_config, config_file, indent=4)
                config_file.truncate()
                console.print(
                    f"[bold yellow]Updated config file with missing fields in:[/bold yellow] {CONFIG_FILE}"
                )

    if not os.path.exists(CUSTOM_FILE):
        with open(CUSTOM_FILE, "w", encoding="utf-8") as config_file:
            config_file.writelines("PUT HERE YOUR COMPLEMENTARY INFO AND INSTRUCTIONS")
        console.print(
            f"[bold green]CUSTOM initialized with empty:[/bold green] {CUSTOM_FILE}"
        )

    # Copy LaTeX template if it doesn't exist
    if os.path.exists(TEMPLATE_SRC) and not os.path.exists(TEMPLATE_DEST):
        shutil.copy(TEMPLATE_SRC, TEMPLATE_DEST)
        console.print(f"[bold green]Template copied to:[/bold green] {TEMPLATE_DEST}")
    elif not os.path.exists(TEMPLATE_SRC):
        console.print(
            f"[bold red]Template source not found at:[/bold red] {TEMPLATE_SRC}"
        )
    else:
        console.print(
            f"[bold yellow]Template already exists in workspace:[/bold yellow] {TEMPLATE_DEST}"
        )

@click.command()
def delete_agents():
    """
    Deletes all OpenAI agents whose names start with 'ResumeCraftr'.
    """
    try:
        console.print("[bold cyan]🔄 Searching for agents starting with 'ResumeCraftr'...[/bold cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[yellow]Processing request...", total=None)
            
            # Call the function to delete agents
            delete_all_resumecraftr_agents()
            
            progress.update(task, description="[bold green]✅ All matching agents deleted successfully![/bold green]")
            progress.stop()

    except Exception as e:
        console.print(f"[bold red]❌ Error while deleting agents: {e}[/bold red]")

cli.add_command(init)
cli.add_command(delete_agents)
cli.add_command(extract_text, name="extract")
cli.add_command(extract_sections, name="extract-sections")
cli.add_command(add_job_description, name="add-job-description")
cli.add_command(optimize_resume, name="optimize")
cli.add_command(generate_pdf, name="toPdf")
cli.add_command(create_cv, name="create-cv")
cli.add_command(add_section, name="add-section")
cli.add_command(show_cv, name="show-cv")
cli.add_command(extract_pdf, name="extract-pdf")
cli.add_command(tex_to_pdf, name="tex-to-pdf")

if __name__ == "__main__":
    cli()
