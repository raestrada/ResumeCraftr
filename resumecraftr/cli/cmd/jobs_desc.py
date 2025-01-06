import os
import json
import click
from rich.console import Console
from rich.prompt import Prompt

console = Console()
CONFIG_FILE = "cv-workspace/resumecraftr.json"
JOBS_DIR = "cv-workspace/job_descriptions"


@click.command()
@click.argument("job_name")
@click.option("--content", "-c", help="Job description content to store.")
@click.option(
    "--file", "-f", type=click.Path(exists=True), help="Path to a job description file."
)
def add_job_description(job_name, content, file):
    """Add a job description by copying content or from a file."""
    os.makedirs(JOBS_DIR, exist_ok=True)

    job_file = os.path.join(JOBS_DIR, f"{job_name}.txt")

    if file:
        with open(file, "r", encoding="utf-8") as f:
            job_content = f.read()
    elif content:
        job_content = content
    else:
        console.print(
            "[bold red]You must provide either --content or --file.[/bold red]"
        )
        return

    with open(job_file, "w", encoding="utf-8") as f:
        f.write(job_content)

    # Update resumecraftr.json
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

    job_list = config.get("job_descriptions", [])
    if os.path.basename(job_file) not in job_list:
        job_list.append(os.path.basename(job_file))
    config["job_descriptions"] = job_list

    with open(CONFIG_FILE, "w", encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=4)

    console.print(f"[bold green]Job description saved: {job_file}[/bold green]")
    console.print(
        f"[bold green]Updated {CONFIG_FILE} with job description reference.[/bold green]"
    )


if __name__ == "__main__":
    add_job_description()
