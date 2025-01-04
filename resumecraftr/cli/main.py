import click
import json
import os
from rich.console import Console
from cli.cmd.pdf import extract_text
from cli.cmd.sections import extract_sections
from cli.cmd.jobs_desc import add_job_description
from cli.cmd.resume import optimize_resume
from cli.cmd.latex import generate_pdf


console = Console()

CONFIG_FILE = "cv-workspace/resumecraftr.json"
DEFAULT_CONFIG = {
    "primary_language": "English",
    "output_format": "pdf"
}

@click.group()
def cli():
    """ResumeCraftr CLI tool"""
    pass

@click.command()
def init():
    """Initialize a new CV workspace"""
    workspace_dir = "cv-workspace"
    os.makedirs(workspace_dir, exist_ok=True)
    
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as config_file:
            json.dump(DEFAULT_CONFIG, config_file, indent=4)
        console.print(f"[bold green]Workspace initialized with default settings in:[/bold green] {CONFIG_FILE}")
    else:
        console.print(f"[bold yellow]Workspace already exists at:[/bold yellow] {CONFIG_FILE}")

cli.add_command(init)
cli.add_command(extract_text, name="extract")
cli.add_command(extract_sections, name="extract-sections")
cli.add_command(add_job_description, name="add-job-description")
cli.add_command(optimize_resume, name="optimize")
cli.add_command(generate_pdf, name="toPdf")



if __name__ == "__main__":
    cli()
