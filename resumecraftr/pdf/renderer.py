from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path

import fitz

from resumecraftr.pdf.document import ResumeDocument, ExperienceEntry, ProjectEntry


@dataclass
class PdfTheme:
    font: str = "helv"
    heading_font: str = "helv"
    bold_font: str = "helv"
    name_size: float = 24
    headline_size: float = 12
    heading_font_size: float = 13
    body_font_size: float = 10.5
    margin: float = 56
    line_height: float = 1.5


class PdfRenderer:
    def __init__(self, theme: PdfTheme | None = None) -> None:
        self.theme = theme or PdfTheme()
        self.doc: fitz.Document | None = None
        self.page: fitz.Page | None = None
        self.cursor: float = 0.0

    # Public API -----------------------------------------------------------------

    def render(self, resume: ResumeDocument, output_path: Path) -> Path:
        self.doc = fitz.open()
        self.page = self.doc.new_page()
        self.cursor = self.theme.margin

        self._draw_header(resume)
        self._draw_summary(resume)
        self._draw_key_strengths(resume)
        self._draw_skills(resume)
        self._draw_experience(resume)
        self._draw_education(resume)
        self._draw_projects(resume)

        assert self.doc is not None
        self.doc.save(str(output_path))
        self.doc.close()
        return output_path

    # Drawing helpers ------------------------------------------------------------

    def _ensure_page(self, extra_height: float = 0) -> None:
        assert self.doc is not None
        assert self.page is not None
        if self.cursor + extra_height < self.page.rect.height - self.theme.margin:
            return
        self.page = self.doc.new_page()
        self.cursor = self.theme.margin

    def _wrap_width(self, indent: float = 0.0) -> int:
        assert self.page is not None
        usable_width = self.page.rect.width - (2 * self.theme.margin) - indent
        avg_char_width = self.theme.body_font_size * 0.55
        return max(40, int(usable_width / avg_char_width))

    def _write_line(self, text: str, font_size: float, indent: float = 0.0, bold: bool = False) -> None:
        if not text:
            return
        assert self.page is not None
        self._ensure_page(font_size * self.theme.line_height)
        self.page.insert_text(
            (self.theme.margin + indent, self.cursor),
            text,
            fontname=self.theme.bold_font if bold else self.theme.font,
            fontsize=font_size,
        )
        self.cursor += font_size * self.theme.line_height

    def _write_paragraph(self, text: str, font_size: float, indent: float = 0.0, width: int = 95) -> None:
        if not text:
            return
        width = self._wrap_width(indent)
        for line in textwrap.wrap(text, width=width):
            self._write_line(line, font_size, indent)

    def _write_section_heading(self, title: str) -> None:
        if not title:
            return
        assert self.page is not None
        self._ensure_page(extra_height=self.theme.heading_font_size * 2)
        self.page.insert_text(
            (self.theme.margin, self.cursor),
            title.upper(),
            fontname=self.theme.heading_font,
            fontsize=self.theme.heading_font_size,
        )
        self.cursor += self.theme.heading_font_size * self.theme.line_height
        self._draw_divider()
        self.cursor += self.theme.body_font_size * 0.2

    def _draw_divider(self) -> None:
        assert self.page is not None
        line_y = self.cursor - (self.theme.heading_font_size * 0.4)
        self.page.draw_line(
            fitz.Point(self.theme.margin, line_y),
            fitz.Point(self.page.rect.width - self.theme.margin, line_y),
        )

    def _write_bullets(self, bullets: list[str], font_size: float, width: int = 90) -> None:
        width = self._wrap_width()
        for bullet in bullets:
            if not bullet:
                continue
            wrapped = textwrap.wrap(bullet, width=width)
            if not wrapped:
                continue
            self._write_line(f"• {wrapped[0]}", font_size)
            for continuation in wrapped[1:]:
                self._write_line(continuation, font_size, indent=14)

    # Section rendering ----------------------------------------------------------

    def _draw_header(self, resume: ResumeDocument) -> None:
        assert self.page is not None
        self._write_line(resume.name, self.theme.name_size, bold=True)
        self._write_line(resume.headline, self.theme.headline_size, bold=True)
        contact = "  |  ".join(resume.contact_lines)
        self._write_paragraph(contact, self.theme.body_font_size)
        self.cursor += self.theme.body_font_size * 0.5
        self._draw_divider()
        self.cursor += self.theme.body_font_size

    def _draw_summary(self, resume: ResumeDocument) -> None:
        self._write_section_heading("Professional Summary")
        self._write_paragraph(resume.summary, self.theme.body_font_size)
        self._write_bullets(resume.summary_highlights, self.theme.body_font_size)
        self.cursor += self.theme.body_font_size

    def _draw_key_strengths(self, resume: ResumeDocument) -> None:
        if not resume.key_strengths:
            return
        self._write_section_heading("Career Highlights")
        self._write_bullets(resume.key_strengths, self.theme.body_font_size)
        self.cursor += self.theme.body_font_size

    def _draw_skills(self, resume: ResumeDocument) -> None:
        if not resume.skills:
            return
        self._write_section_heading("Technical Skills")
        for category, items in resume.skills.items():
            if not items:
                continue
            label = f"{category}: "
            text = ", ".join(items)
            self._write_paragraph(label + text, self.theme.body_font_size, indent=6)
        self.cursor += self.theme.body_font_size

    def _draw_experience(self, resume: ResumeDocument) -> None:
        if not resume.experience:
            return
        self._write_section_heading("Work Experience")
        for entry in resume.experience:
            header = f"{entry.role} | {entry.company}"
            if entry.dates:
                header = f"{header} — {entry.dates}"
            self._write_line(header, self.theme.body_font_size + 1, bold=True)
            self._write_bullets(entry.bullets, self.theme.body_font_size)
            self.cursor += self.theme.body_font_size

    def _draw_education(self, resume: ResumeDocument) -> None:
        if not resume.education:
            return
        self._write_section_heading("Education")
        for entry in resume.education:
            line = entry.institution
            if entry.degree:
                line = f"{line} — {entry.degree}"
            if entry.year:
                line = f"{line} ({entry.year})"
            self._write_line(line, self.theme.body_font_size)
        self.cursor += self.theme.body_font_size

    def _draw_projects(self, resume: ResumeDocument) -> None:
        if not resume.projects:
            return
        self._write_section_heading("Selected Projects")
        for project in resume.projects:
            header = project.name
            self._write_line(header, self.theme.body_font_size + 0.5)
            self._write_paragraph(project.description, self.theme.body_font_size)
            if project.highlights:
                highlight_text = "Tech: " + ", ".join(project.highlights)
                self._write_line(highlight_text, self.theme.body_font_size, indent=10)
            self.cursor += self.theme.body_font_size
