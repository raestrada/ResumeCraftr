import click
import json
import os
from rich.console import Console
from cli.cmd.pdf import extract_text

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

if __name__ == "__main__":
    cli()
