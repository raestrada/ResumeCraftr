import os
import json
import re
import click
import concurrent.futures
import importlib.resources
from rich.prompt import Prompt
from resumecraftr.cli.agent import execute_prompt, create_or_get_agent
from resumecraftr.cli.prompts.sections import RAW_PROMPTS
from resumecraftr.cli.utils.json import clean_json_response
from resumecraftr.cli.utils.costs import confirm_llm_budget
from resumecraftr.cli.utils.naming import slugify, candidate_name_from_sections, candidate_slug
from resumecraftr.cli.ui import console, create_progress, activity
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

SECTION_ALIASES = {
    "Work Experience": ["WORK EXPERIENCE", "PROFESSIONAL EXPERIENCE", "EXPERIENCE"],
    "Projects": ["PROJECTS", "SELECTED PROJECTS"],
    "Summary": ["PROFESSIONAL PROFILE", "PROFILE", "SUMMARY"],
    "Education": ["EDUCATION", "TRAINING"],
    "Technical Skills": ["TECHNICAL SKILLS", "SKILLS"],
}

SECTION_CHUNK_CONFIG = {
    "Work Experience": {"chunk_chars": 3200, "overlap": 400, "merge": "list"},
    "Projects": {"chunk_chars": 2600, "overlap": 300, "merge": "list"},
    "Technical Skills": {"chunk_chars": 2800, "overlap": 300, "merge": "skills"},
    "Publications & Open Source Contributions": {
        "chunk_chars": 2600,
        "overlap": 300,
        "merge": "list",
    },
}


def process_section(config, section_name, text_content, language, chunk_info: str | None = None):
    if section_name not in RAW_PROMPTS:
        console.print(
            f"[bold red]No prompt found for section '{section_name}'. Skipping extraction.[/bold red]"
        )
        return section_name, None

    label = section_name if not chunk_info else f"{section_name} {chunk_info}"
    console.print(f"[cyan]Extracting {label} in {language}...[/cyan]")
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


def build_section_texts(full_text: str, sections_config: dict) -> dict:
    """Return a mapping of section name -> substring using heading-aware matching."""

    positions = []
    for section in sections_config.get("sections", []):
        name = section["name"]
        aliases = SECTION_ALIASES.get(name, [name])
        match_idx = None

        # Pass 1: look for aliases that appear as standalone headings.
        for alias in aliases:
            heading_pattern = re.compile(rf"(?im)^\s*{re.escape(alias)}\s*$")
            match = heading_pattern.search(full_text)
            if match:
                match_idx = match.start()
                break

        # Pass 2: fall back to the first substring match if no heading was found.
        if match_idx is None:
            upper_text = full_text.upper()
            for alias in aliases:
                idx = upper_text.find(alias.upper())
                if idx != -1:
                    match_idx = idx
                    break

        if match_idx is not None:
            positions.append((match_idx, name))

    positions.sort()
    section_text = {}
    for idx, (start, name) in enumerate(positions):
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(full_text)
        section_text[name] = full_text[start:end].strip()
    return section_text


def chunk_text_for_section(section_name: str, text: str) -> list[str]:
    config = SECTION_CHUNK_CONFIG.get(section_name)
    if not config or not text.strip():
        return [text]

    chunk_size = max(config.get("chunk_chars", 3000), 500)
    overlap = min(config.get("overlap", 300), chunk_size - 100)

    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(length, start + chunk_size)
        soft_end = text.rfind("\n\n", start + int(chunk_size * 0.4), end)
        if soft_end != -1 and soft_end > start:
            end = soft_end
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == length:
            break
        start = end - overlap
        if start < 0:
            start = end
    return chunks or [text]


@click.command()
def parse_cv():
    """Parse a CV from a previously imported text file into structured sections."""
    # Load configuration
    if not os.path.exists(CONFIG_FILE):
        console.print(
            "[bold red]Configuration file not found. Run 'resumecraftr setup' first.[/bold red]"
        )
        return

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        workspace_config = json.load(f)

    # Only create the agent when we're about to use OpenAI
    with activity("Loading LangChain runtime"):
        create_or_get_agent()

    extracted_files = workspace_config.get("extracted_files", [])
    language = workspace_config.get("primary_language", "EN")

    if not extracted_files:
        console.print(
            "[bold red]No imported CV files found in configuration.[/bold red]"
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

    console.rule("[bold blue]Parse CV[/bold blue]")
    console.print(f"[bold]Source:[/] {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        text_content = f.read()

    if not os.path.exists(SECTIONS_FILE):
        console.print(
            "[bold red]Sections configuration file not found in templates/sections.json.[/bold red]"
        )
        return

    with open(SECTIONS_FILE, "r", encoding="utf-8") as f:
        sections_config = json.load(f)

    section_text_map = build_section_texts(text_content, sections_config)

    extracted_data = {}

    pending_sections = []
    estimated_chars = 0
    for section_info in sections_config.get("sections", []):
        name = section_info["name"]
        use_full_text = name in SECTION_CHUNK_CONFIG
        base_text = section_text_map.get(name, text_content)
        if use_full_text or not base_text.strip():
            base_text = text_content
        chunks = chunk_text_for_section(name, base_text)
        estimated_chars += sum(len(chunk) for chunk in chunks)
        pending_sections.append((name, chunks))

    from resumecraftr.cli.utils.costs import confirm_llm_budget

    if not confirm_llm_budget("Parse CV", workspace_config, estimated_chars, completion_ratio=0.3):
        console.print("[yellow]Parse cancelled.[/yellow]")
        return

    with concurrent.futures.ThreadPoolExecutor() as executor, create_progress() as progress:
        future_to_section = {}
        section_tasks = {}
        for name, chunks in pending_sections:
            is_chunked = name in SECTION_CHUNK_CONFIG
            total = len(chunks)
            task_id = progress.add_task(f"[cyan]{name}", total=total)
            section_tasks[name] = task_id
            for idx, chunk_text in enumerate(chunks, start=1):
                chunk_label = (
                    f"(chunk {idx}/{total})" if total > 1 and is_chunked else None
                )
                future = executor.submit(
                    process_section,
                    workspace_config,
                    name,
                    chunk_text,
                    language,
                    chunk_label,
                )
                future_to_section[future] = (name, is_chunked, task_id)

        for future in concurrent.futures.as_completed(future_to_section):
            section_name, chunked, task_id = future_to_section[future]
            _, result = future.result()
            progress.advance(task_id)
            if result is None:
                continue
            if chunked:
                extracted_data.setdefault(section_name, [])
                if isinstance(result, list):
                    extracted_data[section_name].extend(result)
                else:
                    extracted_data[section_name].append(result)
            else:
                extracted_data[section_name] = result

    for section_name, value in list(extracted_data.items()):
        chunk_cfg = SECTION_CHUNK_CONFIG.get(section_name)
        if not chunk_cfg:
            continue
        merge_strategy = chunk_cfg.get("merge")
        if merge_strategy == "list" and isinstance(value, list):
            ordered = []
            key_map = {}

            def experience_keys(entry: dict):
                job = (entry.get("Job Title") or "").strip().lower()
                company = (entry.get("Company") or "").strip().lower()
                dates = (entry.get("Dates of Employment") or "").strip().lower()
                keys = []
                if job or company or dates:
                    keys.append((job, company, dates))
                if job or company:
                    keys.append((job, company, ""))
                if not keys:
                    keys.append((json.dumps(entry, sort_keys=True), "", ""))
                return keys

            def publication_key(entry: dict):
                title = (entry.get("Title") or entry.get("name") or "").strip().lower()
                details = (entry.get("Details") or entry.get("description") or "").strip().lower()
                return (title, details)

            is_publications = section_name == "Publications & Open Source Contributions"

            for entry in value:
                if not isinstance(entry, dict):
                    continue
                if is_publications:
                    key = publication_key(entry)
                    if not any(key):
                        continue
                    target = key_map.get(key)
                    if not target:
                        target = {
                            "Title": entry.get("Title") or entry.get("name"),
                            "Details": entry.get("Details") or entry.get("description"),
                        }
                        ordered.append(target)
                        key_map[key] = target
                    continue

                if not any(
                    (entry.get("Job Title"), entry.get("Company"), entry.get("Dates of Employment"), entry.get("Responsibilities"))
                ):
                    continue

                keys = experience_keys(entry)
                target = None
                for key in keys:
                    if key in key_map:
                        target = key_map[key]
                        break
                if target is None:
                    target = {
                        "Job Title": entry.get("Job Title"),
                        "Company": entry.get("Company"),
                        "Dates of Employment": entry.get("Dates of Employment"),
                        "Responsibilities": [],
                    }
                    ordered.append(target)
                    for key in keys:
                        key_map[key] = target
                responsibilities = [
                    resp.strip()
                    for resp in (entry.get("Responsibilities") or [])
                    if resp and resp.strip()
                ]
                seen_resp = set(target["Responsibilities"])
                for resp in responsibilities:
                    if resp not in seen_resp:
                        target["Responsibilities"].append(resp)
                        seen_resp.add(resp)

            extracted_data[section_name] = ordered
        elif merge_strategy == "skills" and isinstance(value, list):
            merged = {
                "Programming Languages": [],
                "Tools and Technologies": [],
            }
            seen_langs = set()
            seen_tools = set()
            for entry in value:
                if not isinstance(entry, dict):
                    continue
                for lang in entry.get("Programming Languages", []) or []:
                    lang_norm = lang.strip()
                    if lang_norm and lang_norm not in seen_langs:
                        seen_langs.add(lang_norm)
                        merged["Programming Languages"].append(lang_norm)
                for tool in entry.get("Tools and Technologies", []) or []:
                    tool_norm = tool.strip()
                    if tool_norm and tool_norm not in seen_tools:
                        seen_tools.add(tool_norm)
                        merged["Tools and Technologies"].append(tool_norm)
            extracted_data[section_name] = merged

    base_label = file_to_process.replace(".txt", "").replace(".extracted_sections.json", "")
    source_slug = slugify(base_label, "cv")
    candidate_name = candidate_name_from_sections(extracted_data, base_label)
    candidate_slug_value = candidate_slug(candidate_name, source_slug)
    output_filename = f"{candidate_slug_value}_{source_slug}.extracted_sections.json"
    output_path = os.path.join("cv-workspace", output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=4, ensure_ascii=False)

    parsed_map = workspace_config.setdefault("parsed_sections", {})
    parsed_map[file_to_process] = output_filename
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(workspace_config, f, indent=2, ensure_ascii=False)

    console.print(
        f"[bold green]Parsed CV sections saved to: {output_path}[/bold green]"
    )


if __name__ == "__main__":
    parse_cv() 
