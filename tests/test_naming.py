import pytest

from resumecraftr.cli.utils.naming import slugify, candidate_name_from_sections, candidate_slug


def test_slugify_basic_and_fallback():
    assert slugify("Senior Software Engineer") == "senior-software-engineer"
    assert slugify("  ") == "cv"
    assert slugify("") == "cv"


def test_slugify_strips_accents_and_symbols():
    assert slugify("José Gómez") == "jose-gomez"
    assert slugify("C++ / C# Developer") == "c-c-developer"


def test_candidate_name_from_sections_prefers_contact():
    sections = {
        "Contact Information": {"Full Name": "Ada Lovelace"},
        "Summary": {"Full Name": "Ignored Name"},
    }
    assert candidate_name_from_sections(sections, fallback="Fallback") == "Ada Lovelace"


def test_candidate_name_from_sections_uses_summary_then_fallback():
    sections = {
        "Summary": {"Full Name": "Grace Hopper"},
    }
    assert candidate_name_from_sections(sections, fallback="Fallback") == "Grace Hopper"

    sections = {}
    assert candidate_name_from_sections(sections, fallback="Fallback") == "Fallback"


@pytest.mark.parametrize(
    "name, fallback, expected",
    [
        ("Ada Lovelace", "cv", "alovelace"),
        ("SingleName", "cv", "singlename"),
        ("", "fallback", "fallback"),
        ("  ", "fallback", "fallback"),
    ],
)
def test_candidate_slug_variants(name, fallback, expected):
    assert candidate_slug(name, fallback) == expected

