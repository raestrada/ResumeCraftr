from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
import re
from typing import Callable, Optional

import click
from rich.prompt import Prompt

from resumecraftr.cli.agent import create_or_get_agent
from resumecraftr.cli.ui import console, activity, create_progress
from resumecraftr.cli.utils.json import clean_json_response
from resumecraftr.cli.utils.costs import confirm_llm_budget
from resumecraftr.pdf.document import (
    ExperienceEntry,
    EducationEntry,
    ProjectEntry,
    PublicationEntry,
    ResumeDocument,
    build_resume_document,
)
from resumecraftr.pdf.html_renderer import HtmlPdfRenderer, get_available_templates
CONFIG_FILE = Path("cv-workspace/resumecraftr.json")


def _slugify(value: str, fallback: str = "resume") -> str:
    if not value:
        return fallback
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return cleaned or fallback


def _candidate_slug(full_name: str) -> str:
    parts = [p for p in re.split(r"\s+", full_name.strip()) if p]
    if not parts:
        return "resume"
    if len(parts) == 1:
        return _slugify(parts[0])
    first = re.sub(r"[^A-Za-z0-9]", "", parts[0][:1]).lower()
    last = _slugify(parts[-1])
    return (first + last) or _slugify(parts[-1])


def _job_slug(config: dict) -> str:
    jobs = config.get("job_descriptions") or []
    if not jobs:
        return "job"
    if len(jobs) == 1:
        choice = jobs[0]
    else:
        choice = Prompt.ask("Select job description for file naming", choices=jobs)
    return _slugify(Path(choice).stem, "job")


def _detect_sections() -> list[str]:
    workspace = Path("cv-workspace")
    candidates = sorted(
        [
            str(path.relative_to(workspace))
            for path in workspace.glob("*.tailored_sections.json")
        ]
    )
    if candidates:
        return candidates
    return sorted(
        [
            str(path.relative_to(workspace))
            for path in workspace.glob("*.optimized_sections.json")
        ]
    )


@click.command()
@click.option(
    "--sections",
    "sections_file",
    type=str,
    help="Relative path to the tailored sections JSON file inside cv-workspace",
)
@click.option("--output", type=click.Path(), help="Destination PDF path")
@click.option(
    "--template",
    "template_name",
    type=str,
    help="HTML template to use for PDF rendering",
)
@click.option(
    "--translate",
    "translation_language",
    type=str,
    help="Translate the resume content to the provided language code before rendering (e.g., ES, FR).",
)
def export_pdf(
    sections_file: str | None,
    output: str | None,
    template_name: str | None,
    translation_language: str | None,
) -> None:
    """Render a resume PDF with PyMuPDF using tailored JSON sections."""

    if not CONFIG_FILE.exists():
        console.print("[bold red]Configuration file missing. Run 'resumecraftr setup'.[/bold red]")
        return

    with CONFIG_FILE.open("r", encoding="utf-8") as fh:
        config = json.load(fh)
    tailored_map = config.get("tailored_files", {})

    available = _detect_sections()
    if not available:
        console.print(
            "[bold red]No tailored sections found. Run 'resumecraftr tailor-cv' first.[/bold red]"
        )
        return

    if sections_file is None:
        if len(available) == 1:
            sections_file = available[0]
        else:
            sections_file = Prompt.ask("Select tailored sections", choices=available)

    sections_path = Path("cv-workspace") / sections_file
    if not sections_path.exists():
        console.print(f"[bold red]Sections file '{sections_file}' not found.[/bold red]")
        return

    with sections_path.open("r", encoding="utf-8") as fh:
        tailored_sections = json.load(fh)

    base_name = sections_path.stem.replace(".tailored_sections", "")
    linked = tailored_map.get(sections_path.name)
    if linked:
        extracted_path = Path("cv-workspace") / linked
    else:
        extracted_path = sections_path.with_name(f"{base_name}.extracted_sections.json")
    if not extracted_path.exists():
        console.print(
            f"[bold red]Original sections file '{extracted_path.name}' not found. Re-run parsing first.[/bold red]"
        )
        return

    with extracted_path.open("r", encoding="utf-8") as fh:
        extracted_sections = json.load(fh)

    resume_document = build_resume_document(extracted_sections, tailored_sections)
    candidate_part = _candidate_slug(resume_document.name)

    if translation_language:
        translation_language = translation_language.strip()
        cache_path = sections_path.with_name(
            f"{sections_path.stem}.{translation_language.lower()}.translated.json"
        )
        resume_document = _translate_resume_document(
            resume_document, translation_language, cache_path, config
        )
    language_slug = (
        (translation_language or config.get("primary_language") or "en").lower()
    )
    workspace_dir = Path("cv-workspace")
    templates = get_available_templates(workspace=workspace_dir)
    if not templates:
        console.print("[bold red]No resume templates found.[/bold red]")
        return

    if template_name is None:
        if len(templates) == 1:
            template_name = templates[0]
        else:
            template_name = Prompt.ask(
                "Select PDF template", choices=templates
            )
    elif template_name not in templates:
        console.print(
            f"[bold red]Template '{template_name}' not found. Available: {', '.join(templates)}[/bold red]"
        )
        return

    renderer = HtmlPdfRenderer(template_name=template_name, workspace=workspace_dir)
    output_dir = Path("cv-workspace/output")
    output_dir.mkdir(exist_ok=True)
    if output:
        output_path = Path(output)
    else:
        template_part = _slugify(template_name, "template")
        job_part = _job_slug(config)
        filename = f"{candidate_part}_{template_part}_{language_slug}_{job_part}.pdf"
        output_path = output_dir / filename

    with activity(f"Rendering {template_name} template"):
        renderer.render(resume_document, output_path)
    console.print(f"[bold green]PDF generated at {output_path}[/bold green]")


def _translate_resume_document(
    resume: ResumeDocument, language: str, cache_path: Path, workspace_config: dict
) -> ResumeDocument:
    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            translated = _resume_from_dict(data, resume)
            console.print(
                f"[bold green]Loaded cached {language.upper()} translation from {cache_path.name}[/bold green]"
            )
            return translated
        except Exception:
            pass

    payload_chars = len(json.dumps(asdict(resume), ensure_ascii=False))
    if not confirm_llm_budget(
        f"Translate resume to {language.upper()}",
        workspace_config,
        payload_chars,
        completion_ratio=1.0,
    ):
        console.print("[yellow]Translation cancelled.[/yellow]")
        return resume

    runtime = create_or_get_agent()
    translator = ResumeTranslator(runtime, language)
    total_units = translator.estimate_units(resume)
    with create_progress(transient=False) as progress:
        task_id = progress.add_task(
            f"[cyan]Translating → {language.upper()}",
            total=total_units or None,
        )

        def advance(label: str) -> None:
            task = progress.tasks[task_id]
            next_value = (task.completed or 0) + 1
            total = task.total
            if total:
                description = f"[cyan]{label} ({int(next_value)}/{int(total)})"
            else:
                description = f"[cyan]{label}"
            progress.update(task_id, advance=1, description=description)

        translated = translator.translate(resume, progress_callback=advance)
    cache_path.write_text(
        json.dumps(asdict(translated), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    console.print(
        f"[bold green]Cached translated resume at {cache_path.name}[/bold green]"
    )
    return translated


def _resume_from_dict(data: dict, fallback: ResumeDocument) -> ResumeDocument:
    def safe_text(value, default: str = "") -> str:
        if isinstance(value, str):
            text = value.strip()
            if text:
                return text
        return default

    def safe_list(values, default):
        if isinstance(values, list):
            cleaned = [str(v).strip() for v in values if isinstance(v, str) and str(v).strip()]
            if cleaned:
                return cleaned
        return default

    skills = fallback.skills
    incoming_skills = data.get("skills")
    if isinstance(incoming_skills, dict):
        skills = {
            "Programming Languages": safe_list(
                incoming_skills.get("Programming Languages"),
                fallback.skills.get("Programming Languages", []),
            ),
            "Tools & Technologies": safe_list(
                incoming_skills.get("Tools & Technologies"),
                fallback.skills.get("Tools & Technologies", []),
            ),
        }

    def build_experience() -> list[ExperienceEntry]:
        entries = []
        source = data.get("experience")
        if isinstance(source, list):
            for entry in source:
                if not isinstance(entry, dict):
                    continue
                entries.append(
                    ExperienceEntry(
                        role=safe_text(entry.get("role"), "Role"),
                        company=safe_text(entry.get("company"), "Company"),
                        dates=safe_text(entry.get("dates"), ""),
                        bullets=safe_list(entry.get("bullets"), []),
                    )
                )
        return entries or fallback.experience

    def build_education() -> list[EducationEntry]:
        entries = []
        source = data.get("education")
        if isinstance(source, list):
            for entry in source:
                if not isinstance(entry, dict):
                    continue
                entries.append(
                    EducationEntry(
                        institution=safe_text(entry.get("institution"), "Institution"),
                        degree=safe_text(entry.get("degree"), ""),
                        year=safe_text(entry.get("year"), ""),
                    )
                )
        return entries or fallback.education

    def build_projects() -> list[ProjectEntry]:
        entries = []
        source = data.get("projects")
        if isinstance(source, list):
            for entry in source:
                if not isinstance(entry, dict):
                    continue
                entries.append(
                    ProjectEntry(
                        name=safe_text(entry.get("name"), "Project"),
                        description=safe_text(entry.get("description"), ""),
                        highlights=safe_list(entry.get("highlights"), []),
                    )
                )
        return entries or fallback.projects

    def build_publications() -> list[PublicationEntry]:
        entries = []
        source = data.get("publications")
        if isinstance(source, list):
            for entry in source:
                if not isinstance(entry, dict):
                    continue
                entries.append(
                    PublicationEntry(
                        title=safe_text(entry.get("title"), "Contribution"),
                        details=safe_text(entry.get("details"), ""),
                    )
                )
        return entries or fallback.publications

    return ResumeDocument(
        name=safe_text(data.get("name"), fallback.name),
        headline=safe_text(data.get("headline"), fallback.headline),
        contact_lines=safe_list(data.get("contact_lines"), fallback.contact_lines),
        summary=safe_text(data.get("summary"), fallback.summary),
        summary_highlights=safe_list(data.get("summary_highlights"), fallback.summary_highlights),
        key_strengths=safe_list(data.get("key_strengths"), fallback.key_strengths),
        skills=skills,
        experience=build_experience(),
        education=build_education(),
        projects=build_projects(),
        publications=build_publications(),
    )


class ResumeTranslator:
    def __init__(self, runtime, language: str) -> None:
        self.runtime = runtime
        self.language = language
        self.cache: dict[str, str] = {}
        self._progress_callback = None

    def estimate_units(self, resume: ResumeDocument) -> int:
        count = 3  # name, headline, summary
        count += len(resume.contact_lines)
        count += len(resume.summary_highlights)
        count += len(resume.key_strengths)
        count += sum(1 for _, values in resume.skills.items() if values)
        count += len(resume.experience)
        count += len(resume.education)
        count += len(resume.projects)
        count += len(resume.publications)
        return max(count, 1)

    def translate(
        self,
        resume: ResumeDocument,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> ResumeDocument:
        self._progress_callback = progress_callback
        return ResumeDocument(
            name=self._translate_text(resume.name, "Name"),
            headline=self._translate_text(resume.headline, "Headline"),
            contact_lines=[
                self._translate_text(line, f"Contact {idx + 1}")
                for idx, line in enumerate(resume.contact_lines)
            ],
            summary=self._translate_text(resume.summary, "Summary"),
            summary_highlights=self._translate_list(
                resume.summary_highlights, "Summary highlights"
            ),
            key_strengths=self._translate_list(
                resume.key_strengths, "Key strengths"
            ),
            skills={
                key: self._translate_list(values, f"{key} skills")
                for key, values in resume.skills.items()
            },
            experience=[
                self._translate_experience(entry, idx)
                for idx, entry in enumerate(resume.experience, start=1)
            ],
            education=[
                self._translate_education(entry, idx)
                for idx, entry in enumerate(resume.education, start=1)
            ],
            projects=[
                self._translate_project(entry, idx)
                for idx, entry in enumerate(resume.projects, start=1)
            ],
            publications=[
                self._translate_publication(entry, idx)
                for idx, entry in enumerate(resume.publications, start=1)
            ],
        )

    def _tick(self, label: str) -> None:
        if self._progress_callback:
            self._progress_callback(label)

    def _translate_text(self, text: str, label: str, tick: bool = True) -> str:
        if not text:
            return text
        cache_key = f"text::{text}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        prompt = (
            "Translate the following resume text into {lang}. "
            "Keep acronyms, numbers, and product names intact when appropriate. "
            'Respond with JSON: {{"text": "<translated>"}}.\n\n{payload}'
        ).format(lang=self.language, payload=text)
        response = self.runtime.run_prompt(prompt)
        if tick:
            self._tick(label)
        parsed = clean_json_response(response)
        if isinstance(parsed, dict) and parsed.get("text"):
            value = parsed["text"].strip()
        else:
            value = response.strip()
        self.cache[cache_key] = value
        return value

    def _translate_list(self, items: list[str], label: str, tick: bool = True) -> list[str]:
        if not items:
            return []
        cache_key = f"list::{json.dumps(items, ensure_ascii=False)}"
        if cache_key in self.cache:
            return json.loads(self.cache[cache_key])
        prompt = (
            "Translate each bullet below into {lang}, preserving order and meaning. "
            "Return a JSON array of translated strings.\n\n{payload}"
        ).format(lang=self.language, payload=json.dumps(items, ensure_ascii=False, indent=2))
        response = self.runtime.run_prompt(prompt)
        if tick:
            self._tick(label)
        parsed = clean_json_response(response)
        if isinstance(parsed, list):
            result = [str(item).strip() for item in parsed if str(item).strip()]
        else:
            result = [self._translate_text(item, label, tick=False) for item in items]
        self.cache[cache_key] = json.dumps(result, ensure_ascii=False)
        return result

    def _translate_experience(self, entry: ExperienceEntry, idx: int) -> ExperienceEntry:
        payload = asdict(entry)
        translated = self._translate_mapping(
            payload,
            ["role", "company", "dates", "bullets"],
            f"Experience {idx}",
        )
        return ExperienceEntry(
            role=translated["role"],
            company=translated["company"],
            dates=translated["dates"],
            bullets=translated["bullets"],
        )

    def _translate_education(self, entry: EducationEntry, idx: int) -> EducationEntry:
        payload = asdict(entry)
        translated = self._translate_mapping(
            payload,
            ["institution", "degree", "year"],
            f"Education {idx}",
        )
        return EducationEntry(
            institution=translated["institution"],
            degree=translated["degree"],
            year=translated["year"],
        )

    def _translate_project(self, entry: ProjectEntry, idx: int) -> ProjectEntry:
        payload = asdict(entry)
        translated = self._translate_mapping(
            payload,
            ["name", "description", "highlights"],
            f"Project {idx}",
        )
        return ProjectEntry(
            name=translated["name"],
            description=translated["description"],
            highlights=translated["highlights"],
        )

    def _translate_publication(self, entry: PublicationEntry, idx: int) -> PublicationEntry:
        payload = asdict(entry)
        translated = self._translate_mapping(
            payload,
            ["title", "details"],
            f"Publication {idx}",
        )
        return PublicationEntry(
            title=translated["title"],
            details=translated["details"],
        )

    def _translate_mapping(self, payload: dict, keys: list[str], label: str) -> dict:
        prompt = (
            "Translate the resume entry below into {lang}. "
            "Keep the same JSON keys {keys} and return only JSON."
        ).format(lang=self.language, keys=", ".join(keys))
        prompt += "\n\n" + json.dumps(payload, ensure_ascii=False, indent=2)
        response = self.runtime.run_prompt(prompt)
        self._tick(label)
        parsed = clean_json_response(response)
        if isinstance(parsed, dict):
            result = {}
            for key in keys:
                value = parsed.get(key)
                if isinstance(value, list):
                    result[key] = [str(item).strip() for item in value if str(item).strip()]
                else:
                    result[key] = str(value).strip() if value is not None else ""
            return result
        # Fallback: translate fields individually
        fallback = {}
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                fallback[key] = self._translate_list(value, label, tick=False)
            else:
                fallback[key] = self._translate_text(
                    str(value) if value else "", label, tick=False
                )
        return fallback


if __name__ == "__main__":
    export_pdf()
