import os
import json
import re
import click
import concurrent.futures
import importlib.resources
from rich.console import Console
from rich.prompt import Prompt
from resumecraftr.cli.agent import execute_prompt, create_or_get_agent
from resumecraftr.cli.prompts.sections import RAW_PROMPTS
from resumecraftr.cli.utils.json import clean_json_response


console = Console()
CONFIG_FILE = os.path.join("cv-workspace", "resumecraftr.json")
try:
    with importlib.resources.path(
        "resumecraftr.templates", "sections.json"
    ) as sections_path:
        SECTIONS_FILE = str(sections_path)
except ModuleNotFoundError:
    console.print(
        "[bold red]Error: Could not locate the sections file inside the installed package.[/bold red]"
    )
OUTPUT_FILE = os.path.join("cv-workspace", "{0}.extracted_sections.json")


def process_section(config, section_name, text_content, language):
    if section_name not in RAW_PROMPTS:
        console.print(
            f"[bold red]No prompt found for section '{section_name}'. Skipping extraction.[/bold red]"
        )
        return section_name, None

    console.print(f"[cyan]Extracting {section_name} in {language}...[/cyan]")
    translated_prompt = (
        f"Extract the following section in {language}:\n\n" + RAW_PROMPTS[section_name]
    )

    raw_result = execute_prompt(
        translated_prompt.format(language=config.get("primary_language"))
        .replace("{{", "{")
        .replace("}}", "}")
        + "\n\n"
        + text_content
    )
    parsed_result = clean_json_response(raw_result)

    if parsed_result is None:
        console.print(
            f"[bold red]Failed to parse JSON for section '{section_name}'. Skipping.[/bold red]"
        )

    return section_name, parsed_result  # Devuelve el objeto JSON o None


@click.command()
def extract_sections():
    """Extract CV sections from a previously processed text file."""
    # Load configuration
    if not os.path.exists(CONFIG_FILE):
        console.print(
            "[bold red]Configuration file not found. Run 'resumecraftr init' first.[/bold red]"
        )
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    create_or_get_agent()

    extracted_files = config.get("extracted_files", [])
    language = config.get("primary_language", "EN")

    if not extracted_files:
        console.print(
            "[bold red]No extracted text files found in configuration.[/bold red]"
        )
        return

    # If multiple files exist, let the user choose
    file_to_process = extracted_files[0]
    if len(extracted_files) > 1:
        file_to_process = Prompt.ask(
            "Multiple files detected. Choose one", choices=extracted_files
        )

    file_path = os.path.join("cv-workspace", file_to_process)
    if not os.path.exists(file_path):
        console.print(
            f"[bold red]Selected file '{file_to_process}' does not exist.[/bold red]"
        )
        return

    console.print(f"[bold blue]Processing file: {file_path}[/bold blue]")

    with open(file_path, "r", encoding="utf-8") as f:
        text_content = f.read()

    if not os.path.exists(SECTIONS_FILE):
        console.print(
            "[bold red]Sections configuration file not found in templates/sections.json.[/bold red]"
        )
        return

    with open(SECTIONS_FILE, "r", encoding="utf-8") as f:
        sections_config = json.load(f)

    extracted_data = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_section = {
            executor.submit(
                process_section, config, section_info["name"], text_content, language
            ): section_info["name"]
            for section_info in sections_config.get("sections", [])
        }

        for future in concurrent.futures.as_completed(future_to_section):
            section_name, result = future.result()
            if result is not None:  # Solo guardar si es JSON válido
                extracted_data[section_name] = result

    output_path = OUTPUT_FILE.format(
        file_to_process.replace(".txt", "").replace(".extracted_sections.json", "")
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=4, ensure_ascii=False)

    console.print(
        f"[bold green]Extracted sections saved to: {output_path}[/bold green]"
    )


if __name__ == "__main__":
    extract_sections()
