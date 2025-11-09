import re
from typing import Any, Dict


def slugify(value: str, fallback: str = "cv") -> str:
    if not value:
        return fallback
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return cleaned or fallback


def candidate_name_from_sections(sections: Dict[str, Any], fallback: str) -> str:
    contact = sections.get("Contact Information")
    if isinstance(contact, dict):
        name = contact.get("Full Name") or contact.get("Name")
        if isinstance(name, str) and name.strip():
            return name.strip()

    summary = sections.get("Summary")
    if isinstance(summary, dict):
        name = summary.get("Full Name")
        if isinstance(name, str) and name.strip():
            return name.strip()

    return fallback


def candidate_slug(name: str, fallback: str) -> str:
    parts = [p for p in re.split(r"\s+", (name or "").strip()) if p]
    if not parts:
        return slugify(fallback)
    if len(parts) == 1:
        return slugify(parts[0])
    first = re.sub(r"[^A-Za-z0-9]", "", parts[0][:1]).lower()
    last = slugify(parts[-1])
    combined = (first + last).strip("-")
    return combined or slugify(last)
