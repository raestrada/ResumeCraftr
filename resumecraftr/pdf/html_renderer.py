from __future__ import annotations

from pathlib import Path
import importlib.resources as resources
from typing import List

import fitz

from resumecraftr.pdf.document import ResumeDocument


class HtmlPdfRenderer:
    def __init__(self, template_name: str = "modern", workspace: Path | None = None) -> None:
        self.template_name = template_name
        self.workspace = workspace or Path("cv-workspace")

    def render(self, resume: ResumeDocument, output_path: Path) -> Path:
        template = self._load_template()
        html = template.render(resume=resume)
        html_doc = fitz.open("html", html.encode("utf-8"))
        pdf_bytes = html_doc.convert_to_pdf()
        pdf_doc = fitz.open("pdf", pdf_bytes)
        pdf_doc.save(str(output_path))
        pdf_doc.close()
        html_doc.close()
        return output_path

    def _load_template(self):
        from jinja2 import Template

        template_file = f"{self.template_name}.html"
        search_paths = list(_workspace_template_dirs(self.workspace))
        search_paths.append(resources.files("resumecraftr.pdf.templates"))

        for base in search_paths:
            tpl_path = base / template_file
            if tpl_path.is_file():
                return Template(tpl_path.read_text(encoding="utf-8"))

        available = ", ".join(get_available_templates(self.workspace))
        raise FileNotFoundError(
            f"Template '{self.template_name}' not found. Available templates: {available}"
        )


def _workspace_template_dirs(workspace: Path) -> List[Path]:
    custom_dir = workspace / "templates" / "pdf"
    if custom_dir.exists():
        return [custom_dir]
    return []


def get_available_templates(workspace: Path | None = None) -> List[str]:
    workspace = workspace or Path("cv-workspace")
    seen = set()
    templates = []

    for base in _workspace_template_dirs(workspace):
        for path in base.glob("*.html"):
            if path.is_file() and path.stem not in seen:
                seen.add(path.stem)
                templates.append(path.stem)

    bundled = resources.files("resumecraftr.pdf.templates")
    for path in bundled.iterdir():
        if path.suffix == ".html" and path.is_file() and path.stem not in seen:
            seen.add(path.stem)
            templates.append(path.stem)

    return sorted(templates)
