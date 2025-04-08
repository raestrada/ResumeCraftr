import os
import click
from rich.console import Console
from resumecraftr.cli.cmd.setup import setup
from resumecraftr.cli.cmd.import_cv import import_cv
from resumecraftr.cli.cmd.parse_cv import parse_cv
from resumecraftr.cli.cmd.add_job import add_job
from resumecraftr.cli.cmd.tailor_cv import tailor_cv
from resumecraftr.cli.cmd.export_pdf import export_pdf
from resumecraftr.cli.cmd.new_cv import new_cv, edit_section, view_cv

console = Console()

@click.group()
def cli():
    """ResumeCraftr - A tool for creating and managing ATS-friendly resumes."""
    pass

# Register commands
cli.add_command(setup)
cli.add_command(import_cv)
cli.add_command(parse_cv)
cli.add_command(add_job)
cli.add_command(tailor_cv)
cli.add_command(export_pdf)
cli.add_command(new_cv)
cli.add_command(edit_section)
cli.add_command(view_cv)

if __name__ == "__main__":
    cli()
