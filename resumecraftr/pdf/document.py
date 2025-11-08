from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any


def _clean_list(values: Any) -> List[str]:
    if isinstance(values, list):
        return [str(v).strip() for v in values if str(v).strip()]
    return []


def _clean_text(value: Any, fallback: str = "") -> str:
    if isinstance(value, str):
        return value.strip()
    return fallback


@dataclass
class ExperienceEntry:
    role: str
    company: str
    dates: str
    bullets: List[str] = field(default_factory=list)


@dataclass
class EducationEntry:
    institution: str
    degree: str
    year: str


@dataclass
class ProjectEntry:
    name: str
    description: str
    highlights: List[str]


@dataclass
class PublicationEntry:
    title: str
    details: str


@dataclass
class ResumeDocument:
    name: str
    headline: str
    contact_lines: List[str]
    summary: str
    summary_highlights: List[str]
    key_strengths: List[str]
    skills: Dict[str, List[str]]
    experience: List[ExperienceEntry]
    education: List[EducationEntry]
    projects: List[ProjectEntry]
    publications: List[PublicationEntry]


def build_resume_document(extracted: Dict, tailored: Dict) -> ResumeDocument:
    contact = extracted.get("Contact Information", {})
    name = _clean_text(contact.get("Full Name"), "Candidate Name")

    raw_summary = extracted.get("Summary", {})
    original_summary = _clean_text(raw_summary.get("Summary"))

    tailored_summary = tailored.get("Summary", {})
    summary_text = _clean_text(
        tailored_summary.get("summary") if isinstance(tailored_summary, dict) else None,
        original_summary,
    )
    summary_highlights = _clean_list(
        tailored_summary.get("highlights", []) if isinstance(tailored_summary, dict) else []
    )

    headline = contact.get("Title") or original_summary or summary_text.split(".")[0]
    headline = _clean_text(headline, "Principal Software Engineer")

    work_tailored = tailored.get("Work Experience")
    if isinstance(work_tailored, dict):
        key_strengths = _clean_list(work_tailored.get("highlights", []))
    else:
        key_strengths = []

    skills_section = extracted.get("Technical Skills", {})
    skills = {
        "Programming Languages": _clean_list(skills_section.get("Programming Languages", [])),
        "Tools & Technologies": _clean_list(skills_section.get("Tools and Technologies", [])),
    }

    experience_entries: List[ExperienceEntry] = []
    for entry in extracted.get("Work Experience", []) or []:
        if not isinstance(entry, dict):
            continue
        experience_entries.append(
            ExperienceEntry(
                role=_clean_text(entry.get("Job Title"), "Role"),
                company=_clean_text(entry.get("Company"), "Company"),
                dates=_clean_text(entry.get("Dates of Employment"), ""),
                bullets=_clean_list(entry.get("Responsibilities", [])),
            )
        )

    education_entries: List[EducationEntry] = []
    for entry in extracted.get("Education", []) or []:
        if not isinstance(entry, dict):
            continue
        education_entries.append(
            EducationEntry(
                institution=_clean_text(entry.get("Institution"), "Institution"),
                degree=_clean_text(entry.get("Degree"), ""),
                year=_clean_text(entry.get("Year"), ""),
            )
        )

    project_entries: List[ProjectEntry] = []
    for entry in extracted.get("Projects", []) or []:
        if not isinstance(entry, dict):
            continue
        project_entries.append(
            ProjectEntry(
                name=_clean_text(entry.get("Project Name"), "Project"),
                description=_clean_text(entry.get("Description"), ""),
                highlights=_clean_list(entry.get("Technologies Used", [])),
            )
        )

    publication_entries: List[PublicationEntry] = []
    publications_raw = extracted.get("Publications & Open Source Contributions")
    if isinstance(publications_raw, list):
        for entry in publications_raw:
            if not isinstance(entry, dict):
                continue
            publication_entries.append(
                PublicationEntry(
                    title=_clean_text(entry.get("Title") or entry.get("name"), "Contribution"),
                    details=_clean_text(entry.get("Details") or entry.get("description")),
                )
            )
    elif isinstance(publications_raw, dict):
        publication_entries.append(
            PublicationEntry(
                title=_clean_text(publications_raw.get("summary"), "Contribution"),
                details=_clean_text(publications_raw.get("details") or ""),
            )
        )

    contact_lines = []
    labels = [
        ("Email", contact.get("Email")),
        ("Phone", contact.get("Phone Number")),
        ("LinkedIn", contact.get("LinkedIn")),
        ("GitHub", contact.get("GitHub")),
        ("Portfolio", contact.get("Portfolio")),
        ("Location", contact.get("Location")),
    ]
    for label, value in labels:
        if value:
            contact_lines.append(f"{label}: {value}")

    return ResumeDocument(
        name=name,
        headline=headline,
        contact_lines=contact_lines,
        summary=summary_text,
        summary_highlights=summary_highlights,
        key_strengths=key_strengths,
        skills=skills,
        experience=experience_entries,
        education=education_entries,
        projects=project_entries,
        publications=publication_entries,
    )
