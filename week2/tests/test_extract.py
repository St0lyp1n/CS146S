import os

import httpx
import pytest

from ..app.services.extract import extract_action_items, extract_action_items_llm


def _ollama_available() -> bool:
    """Return True when the local Ollama server responds."""
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        response = httpx.get(f"{host.rstrip('/')}/api/tags", timeout=5.0, trust_env=False)
        return response.status_code == 200
    except (httpx.HTTPError, OSError):
        return False


def _assert_contains_item(items: list[str], expected: str) -> None:
    """Match action items case-insensitively (LLM wording may vary slightly)."""
    needle = expected.lower()
    assert any(needle in item.lower() for item in items), (
        f"Expected an item containing {expected!r}, got {items!r}"
    )


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


def test_extract_action_items_llm_empty_input():
    assert extract_action_items_llm("") == []
    assert extract_action_items_llm("   \n\t  ") == []


@pytest.mark.skipif(
    not _ollama_available(),
    reason="Ollama is not running; start it or set OLLAMA_HOST",
)
def test_extract_action_items_llm_bullet_list():
    text = """
    Sprint notes:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    We discussed timelines but no decision yet.
    """.strip()

    items = extract_action_items_llm(text)

    assert len(items) >= 3
    _assert_contains_item(items, "database")
    _assert_contains_item(items, "API")
    _assert_contains_item(items, "tests")


@pytest.mark.skipif(
    not _ollama_available(),
    reason="Ollama is not running; start it or set OLLAMA_HOST",
)
def test_extract_action_items_llm_keyword_prefixed_lines():
    text = """
    Standup:
    TODO: Review pull request
    action: Deploy staging environment
    next: Schedule retrospective
    General discussion only.
    """.strip()

    items = extract_action_items_llm(text)

    assert len(items) >= 3
    _assert_contains_item(items, "pull request")
    _assert_contains_item(items, "staging")
    _assert_contains_item(items, "retrospective")
