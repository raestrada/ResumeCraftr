import os
import json
import click
import concurrent.futures
from rich.console import Console
from rich.prompt import Prompt
from resumecraftr.cli.agent import execute_prompt, create_or_get_agent
from resumecraftr.cli.prompts.resume import RAW_PROMPTS
from resumecraftr.cli.utils.json import clean_json_response, merge_json_files

console = Console()
CONFIG_FILE = "cv-workspace/resumecraftr.json"
OUTPUT_FILE = "cv-workspace/{0}.optimized_sections.json"


def optimize_section(config, section_name, content, job_description):
    """
    Llama a OpenAI para optimizar la sección del CV en base a la descripción del trabajo.
    """

    prompt = (
        RAW_PROMPTS["optimize_resume"].format(language=config.get("primary_language"))
        + "\n\n"
        + json.dumps(
            {
                "section_name": section_name,
                "section_content": content,
                "job_description": job_description,
            },
            indent=4,
        )
    )

    raw_result = execute_prompt(prompt)
    parsed_result = clean_json_response(raw_result)

    if parsed_result is None:
        console.print(
            f"[bold red]Failed to parse JSON for section '{section_name}'. Skipping.[/bold red]"
        )

    return section_name, parsed_result  # Devuelve el JSON limpio o None


@click.command()
def optimize_resume():
    """Optimize a resume based on a job description."""
    # Cargar configuración
    if not os.path.exists(CONFIG_FILE):
        console.print(
            "[bold red]Configuration file not found. Run 'resumecraftr init' first.[/bold red]"
        )
        return

    create_or_get_agent()

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    job_descriptions = config.get("job_descriptions", [])
    extracted_files = config.get("extracted_files", [])

    if not extracted_files:
        console.print(
            "[bold red]No extracted CV sections found in configuration.[/bold red]"
        )
        return

    if not job_descriptions:
        console.print(
            "[bold red]No job descriptions found in configuration.[/bold red]"
        )
        return

    # Seleccionar archivos
    extracted_files = [
        f.replace(".txt", ".extracted_sections.json") for f in extracted_files
    ]
    sections_file = extracted_files[0]
    job_desc_file = job_descriptions[0]

    if len(extracted_files) > 1:
        sections_file = Prompt.ask(
            "Multiple extracted CV files detected. Choose one", choices=extracted_files
        )

    if len(job_descriptions) > 1:
        job_desc_file = Prompt.ask(
            "Multiple job descriptions detected. Choose one", choices=job_descriptions
        )

    sections_path = os.path.abspath(os.path.join("cv-workspace", sections_file))
    job_desc_path = os.path.abspath(
        os.path.join("cv-workspace", "job_descriptions", job_desc_file)
    )

    if not os.path.exists(sections_path):
        console.print(
            f"[bold red]Selected CV sections file '{sections_file}' does not exist.[/bold red]"
        )
        return

    if not os.path.exists(job_desc_path):
        console.print(
            f"[bold red]Selected job description file '{job_desc_file}' does not exist.[/bold red]"
        )
        return

    console.print(
        f"[bold blue]Optimizing resume using: {sections_file} and {job_desc_file}[/bold blue]"
    )

    with open(sections_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            console.print(
                f"[bold red]Error: The CV sections file '{sections_file}' is empty.[/bold red]"
            )
            return
        try:
            sections_content = json.loads(content)
        except json.JSONDecodeError as e:
            console.print(
                f"[bold red]Error: The CV sections file '{sections_file}' is not a valid JSON file.\nDetails: {e}[bold red]"
            )
            return

    with open(job_desc_path, "r", encoding="utf-8") as f:
        job_description = f.read()

    console.print("[cyan]Processing optimization in parallel...[/cyan]")

    optimized_resume = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_section = {
            executor.submit(
                optimize_section, config, section, content, job_description
            ): section
            for section, content in sections_content.items()
        }

        for future in concurrent.futures.as_completed(future_to_section):
            section_name, result = future.result()
            if result is not None:  # Solo guardar si es JSON válido
                optimized_resume[section_name] = result

    output_path = OUTPUT_FILE.format(
        sections_file.replace(".txt", "").replace(".extracted_sections.json", "")
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(optimized_resume, f, indent=4, ensure_ascii=False)

    merge_json_files(output_path, sections_path, output_path)

    console.print(f"[bold green]Optimized resume saved to: {output_path}[/bold green]")


if __name__ == "__main__":
    optimize_resume()
