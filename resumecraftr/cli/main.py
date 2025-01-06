import click
import json
import os
import shutil
from rich.console import Console
from resumecraftr.cli.cmd.pdf import extract_text
from resumecraftr.cli.cmd.sections import extract_sections
from resumecraftr.cli.cmd.jobs_desc import add_job_description
from resumecraftr.cli.cmd.resume import optimize_resume
from resumecraftr.cli.cmd.latex import generate_pdf

console = Console()

CONFIG_FILE = "cv-workspace/resumecraftr.json"
TEMPLATE_SRC = "templates/resume_template.tex"
TEMPLATE_DEST = "cv-workspace/resume_template.tex"

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
def init(language):
    """Initialize a new CV workspace with an optional language setting"""
    workspace_dir = "cv-workspace"
    os.makedirs(workspace_dir, exist_ok=True)

    # Validar el idioma
    language = language.upper()
    if language not in ["EN", "ES"]:
        console.print(
            f"[bold red]Invalid language option:[/bold red] {language}. Use 'EN' or 'ES'."
        )
        return

    # Configuración inicial
    config = DEFAULT_CONFIG.copy()
    config["primary_language"] = language

    # Guardar configuración
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

    # Copiar plantilla LaTeX si no existe
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


cli.add_command(init)
cli.add_command(extract_text, name="extract")
cli.add_command(extract_sections, name="extract-sections")
cli.add_command(add_job_description, name="add-job-description")
cli.add_command(optimize_resume, name="optimize")
cli.add_command(generate_pdf, name="toPdf")

if __name__ == "__main__":
    cli()
