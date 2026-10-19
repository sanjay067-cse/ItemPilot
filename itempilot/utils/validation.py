"""Validation and text formatting utilities for ItemPilot."""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from itempilot.utils.export import build_export_html, build_export_txt

MAX_TITLE_LENGTH = 80


def enforce_title_length(title: str, max_chars: int = MAX_TITLE_LENGTH) -> str:
    """Ensure a title does not exceed max_chars.

    If it does, truncates gracefully on word boundaries where possible.
    """
    if not title:
        return ""

    cleaned = " ".join(title.strip().split())
    if len(cleaned) <= max_chars:
        return cleaned

    # Try truncating at last whitespace before max_chars
    truncated = cleaned[:max_chars].rstrip()
    last_space = truncated.rfind(" ")
    if last_space > (max_chars // 2):
        return truncated[:last_space].rstrip()

    return cleaned[:max_chars].rstrip()


def validate_title_length(title: str, max_chars: int = MAX_TITLE_LENGTH) -> Tuple[bool, Optional[str]]:
    """Validate that title is non-empty and does not exceed max_chars."""
    if not title or not title.strip():
        return False, "Title cannot be empty."
    length = len(title.strip())
    if length > max_chars:
        return False, f"Title has {length} characters, exceeding the {max_chars}-character eBay limit."
    return True, None


def detect_missing_fields(
    item_specifics: Dict[str, Any],
    recommended_keys: Optional[List[str]] = None
) -> List[str]:
    """Identify recommended item specifics that are null, empty, or absent."""
    if recommended_keys is None:
        recommended_keys = ["brand", "model", "color", "condition", "material", "size"]

    missing: List[str] = []
    for key in recommended_keys:
        val = item_specifics.get(key)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(key)
    return missing


def extract_json_from_text(text: str) -> str:
    """Extract a JSON object substring from raw model output.

    Handles markdown code fences (```json ... ```) or raw text with outer braces.
    """
    if not text:
        return ""

    # Check for markdown code fences
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(fence_pattern, text, re.IGNORECASE)
    if match:
        candidate = match.group(1).strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            return candidate

    # Find the first '{' and last '}'
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1].strip()

    return text.strip()


def parse_and_clean_json(text: str) -> Dict[str, Any]:
    """Parse JSON string safely after extracting object substring."""
    cleaned = extract_json_from_text(text)
    if not cleaned:
        raise ValueError("No JSON content detected in model response.")
    return json.loads(cleaned)
