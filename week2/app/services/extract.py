from __future__ import annotations

import os
import re
from typing import List

from dotenv import load_dotenv
from ollama import Client
from pydantic import BaseModel, Field

load_dotenv()

# Small, efficient model suitable for structured extraction (see https://ollama.com/library).
DEFAULT_OLLAMA_MODEL = "llama3.2:3b"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"

# trust_env=False avoids routing local requests through a system HTTP proxy (502 on Windows).
_ollama_client = Client(
    host=os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST),
    trust_env=False,
)


class ActionItemsResponse(BaseModel):
    """JSON schema for Ollama structured output: array of action item strings."""

    action_items: list[str] = Field(
        description="Action items extracted from the notes, without bullet markers or checkboxes."
    )

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def extract_action_items(text: str) -> List[str]:
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters


def extract_action_items_llm(text: str) -> List[str]:
    """Extract action items from free-form notes using an Ollama LLM with structured JSON output."""
    stripped = text.strip()
    if not stripped:
        return []

    model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)

    response = _ollama_client.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract actionable tasks from meeting notes and to-do lists. "
                    "Return each item as a concise imperative phrase. "
                    "Ignore narrative text that is not an action item. "
                    "Return as JSON."
                ),
            },
            {
                "role": "user",
                "content": stripped,
            },
        ],
        format=ActionItemsResponse.model_json_schema(),
        options={"temperature": 0},
    )

    parsed = ActionItemsResponse.model_validate_json(response.message.content)

    # Deduplicate while preserving order (same behavior as extract_action_items).
    seen: set[str] = set()
    unique: List[str] = []
    for item in parsed.action_items:
        cleaned = item.strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(cleaned)
    return unique
