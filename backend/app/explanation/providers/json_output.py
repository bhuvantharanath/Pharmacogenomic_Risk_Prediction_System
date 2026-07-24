"""
Turning whatever a model emitted into a validated schema object.

Different models return JSON differently. A native structured-output model
returns a clean object. An instruction-tuned model wraps it in a ```json fence.
A reasoning model prepends a `<think>…</think>` monologue. A chatty one adds
"Here is the explanation:" before the brace. This module absorbs all of that so
the providers do not each reinvent it, and so a model is judged on the content
of its JSON rather than on how neatly it delivered it.

The recovery ladder is deliberately ordered least-invasive first, and every
provider records which rung worked (`json_mode`) so a model's quirks stay
visible in the benchmark rather than being silently smoothed over.
"""

from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

#: Reasoning blocks some models emit before their answer. Matched non-greedily
#: and case-insensitively; unclosed `<think>` (truncated output) is handled by
#: the second pattern, which drops everything up to a closing tag if the opening
#: one is present.
_THINK_BLOCK = re.compile(r"<think\b[^>]*>.*?</think\s*>", re.IGNORECASE | re.DOTALL)
_THINK_OPEN = re.compile(r"<think\b[^>]*>.*", re.IGNORECASE | re.DOTALL)

#: A ```json … ``` (or bare ``` … ```) fenced block.
_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)


def strip_think(text: str) -> str:
    """
    Remove `<think>…</think>` reasoning blocks.

    Handles the truncated case too: if a model opened a think block and ran out
    of tokens before closing it, everything from the opening tag on is dropped
    rather than left to poison JSON extraction.
    """
    text = _THINK_BLOCK.sub("", text)
    # A leftover opening tag with no close means the reasoning was cut off; the
    # answer (if any) came before it, so drop from the tag onward.
    text = _THINK_OPEN.sub("", text)
    return text.strip()


def extract_json_text(text: str) -> str | None:
    """
    Find the JSON object inside arbitrary model output.

    Tries, in order: a fenced block; then the widest brace-balanced span. Returns
    the candidate string, or None if nothing bracelike is present. Does not
    validate — that is the caller's job, so a malformed candidate produces a
    schema error the caller can report rather than a silent None here.
    """
    cleaned = strip_think(text).strip()
    if not cleaned:
        return None

    fenced = _FENCE.search(cleaned)
    if fenced:
        candidate = fenced.group(1).strip()
        if candidate:
            return candidate

    # Widest balanced {...}. Scanning for the first '{' and last '}' would break
    # on trailing prose containing a brace; balance-counting from the first '{'
    # is robust to a model that appended a sign-off after the object.
    start = cleaned.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return cleaned[start : i + 1]
    # Unbalanced — likely truncated. Hand back what we have so the caller's
    # parse error is about the real problem (truncation) rather than "no JSON".
    return cleaned[start:]


def parse_into(schema: type[T], text: str) -> T:
    """
    Extract and validate model output into `schema`.

    Raises ValueError with a short, key-free reason on any failure. The reason
    names the failure mode (no JSON found / not valid JSON / schema mismatch) so
    a benchmark row or a fallback record says something useful.
    """
    candidate = extract_json_text(text)
    if candidate is None:
        raise ValueError("no JSON object found in model output")
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"output was not valid JSON ({exc.msg})") from exc
    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object, got {type(data).__name__}")
    try:
        return schema.model_validate(data)
    except Exception as exc:  # noqa: BLE001 — pydantic ValidationError et al.
        # Keep it to the field summary; the full repr is noisy and can echo the
        # model's text back into logs.
        missing = _missing_fields(schema, data)
        detail = f"missing/invalid fields: {missing}" if missing else "did not match schema"
        raise ValueError(f"output {detail}") from exc


def _missing_fields(schema: type[BaseModel], data: dict) -> list[str]:
    required = {
        name
        for name, field in schema.model_fields.items()
        if field.is_required()
    }
    return sorted(name for name in required if not str(data.get(name, "")).strip())
