"""Configuration settings for ItemPilot."""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
PROMPTS_DIR = BASE_DIR / "prompts"
LISTING_PROMPT_PATH = PROMPTS_DIR / "listing_prompt.txt"

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL = os.getenv("ITEMPILOT_MODEL", "gemma3:4b")
REQUEST_TIMEOUT = int(os.getenv("ITEMPILOT_TIMEOUT", "120"))

# Validation settings
MAX_TITLE_LENGTH = 80
MAX_IMAGE_SIZE_MB = 10.0
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def get_supported_extensions() -> list[str]:
    """Get list of allowed image extensions without leading dots e.g. ['jpeg', 'jpg', 'png', 'webp']."""
    return sorted(ext.lstrip(".") for ext in ALLOWED_IMAGE_EXTENSIONS)


def get_supported_formats_display() -> str:
    """Format allowed extensions into clean uppercase list e.g. 'JPG, PNG, WEBP'."""
    seen = set()
    formats = []
    for ext in sorted(ALLOWED_IMAGE_EXTENSIONS):
        clean = ext.lstrip(".").upper()
        if clean == "JPEG":
            clean = "JPG"
        if clean not in seen:
            seen.add(clean)
            formats.append(clean)
    return ", ".join(formats)


def get_upload_limit_text() -> str:
    """Generate upload limit text dynamically from configuration e.g. 'Up to 10 MB per file · JPG, PNG, WEBP'."""
    size_str = (
        f"{int(MAX_IMAGE_SIZE_MB)} MB"
        if isinstance(MAX_IMAGE_SIZE_MB, int) or MAX_IMAGE_SIZE_MB.is_integer()
        else f"{MAX_IMAGE_SIZE_MB} MB"
    )
    return f"Up to {size_str} per file \u00b7 {get_supported_formats_display()}"


__all__ = [
    "BASE_DIR",
    "ROOT_DIR",
    "PROMPTS_DIR",
    "LISTING_PROMPT_PATH",
    "OLLAMA_BASE_URL",
    "DEFAULT_MODEL",
    "REQUEST_TIMEOUT",
    "MAX_TITLE_LENGTH",
    "MAX_IMAGE_SIZE_MB",
    "ALLOWED_IMAGE_EXTENSIONS",
    "ALLOWED_MIME_TYPES",
    "get_supported_extensions",
    "get_supported_formats_display",
    "get_upload_limit_text",
]
