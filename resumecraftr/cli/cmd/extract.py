import os
import json
import click
from rich.console import Console
from rich.prompt import Prompt
from resumecraftr.cli.agent import execute_prompt, create_or_get_agent
from resumecraftr.cli.prompts.resume import RAW_PROMPTS
from resumecraftr.cli.utils.json import clean_json_response
from resumecraftr.cli.utils.naming import slugify, candidate_name_from_sections, candidate_slug
from resumecraftr.cli.utils.naming import slugify, candidate_name_from_sections, candidate_slug

console = Console()
CONFIG_FILE = os.path.join("cv-workspace", "resumecraftr.json")

def extract_sections_from_cv(config, cv_content):
    """
    Extract sections from a CV using OpenAI.
    """
    prompt = (
        RAW_PROMPTS["extract_sections"].format(language=config.get("primary_language"))
        + "\n\n"
        + cv_content
    )

    raw_result = execute_prompt(prompt)
    parsed_result = clean_json_response(raw_result)

    if parsed_result is None:
        console.print("[bold red]Failed to parse JSON response. Aborting.[/bold red]")
        return None

    return parsed_result


@click.command()
@click.option("--dummy", is_flag=True, help="Create a dummy CV without extraction")
def extract_sections(dummy):
    """Extract sections from a CV."""
    if not os.path.exists(CONFIG_FILE):
        console.print(
            "[bold red]Configuration file not found. Run 'resumecraftr init' first.[/bold red]"
        )
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    if dummy:
        # Create a dummy CV sections file
        dummy_sections = {
            "personal_info": {},
            "summary": "",
            "experience": [],
            "education": [],
            "skills": [],
            "languages": [],
            "certifications": [],
            "projects": [],
            "interests": []
        }
        
        counter = 1
        while True:
            source_slug = slugify(f"dummy-{counter}", "dummy")
            candidate_slug_value = candidate_slug("Dummy Candidate", source_slug)
            output_filename = f"{candidate_slug_value}_{source_slug}.extracted_sections.json"
            output_file = os.path.join("cv-workspace", output_filename)
            if not os.path.exists(output_file):
                break
            counter += 1
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(dummy_sections, f, indent=4, ensure_ascii=False)
        
        # Update config
        if "extracted_files" not in config:
            config["extracted_files"] = []
        text_entry = f"{source_slug}.txt"
        config["extracted_files"].append(text_entry)
        parsed_map = config.setdefault("parsed_sections", {})
        parsed_map[text_entry] = output_filename
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        console.print(f"[bold green]Created dummy CV sections file: {output_file}[/bold green]")
        return

    # Only create the agent when we're about to use OpenAI
    create_or_get_agent()

    cv_files = [f for f in os.listdir("cv-workspace") if f.endswith(".txt") and not f.startswith("dummy")]

    if not cv_files:
        console.print("[bold red]No CV files found in cv-workspace directory.[/bold red]")
        return

    if len(cv_files) > 1:
        cv_file = Prompt.ask("Multiple CV files detected. Choose one", choices=cv_files)
    else:
        cv_file = cv_files[0]

    cv_path = os.path.join("cv-workspace", cv_file)

    with open(cv_path, "r", encoding="utf-8") as f:
        cv_content = f.read()

    console.print("[cyan]Extracting sections from CV...[/cyan]")
    sections = extract_sections_from_cv(config, cv_content)

    if sections is None:
        return

    base_label = os.path.splitext(cv_file)[0]
    source_slug = slugify(base_label, "cv")
    candidate_name = candidate_name_from_sections(sections, base_label)
    candidate_slug_value = candidate_slug(candidate_name, source_slug)
    output_filename = f"{candidate_slug_value}_{source_slug}.extracted_sections.json"
    output_file = os.path.join("cv-workspace", output_filename)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sections, f, indent=4, ensure_ascii=False)

    if "extracted_files" not in config:
        config["extracted_files"] = []
    config["extracted_files"].append(cv_file)
    parsed_map = config.setdefault("parsed_sections", {})
    parsed_map[cv_file] = output_filename

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    console.print(f"[bold green]Sections extracted and saved to: {output_file}[/bold green]") 
