"""ItemPilot - Local AI eBay Listing Assistant."""

from itempilot.config import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    DEFAULT_MODEL,
    MAX_IMAGE_SIZE_MB,
    MAX_TITLE_LENGTH,
    OLLAMA_BASE_URL,
    REQUEST_TIMEOUT,
    get_supported_extensions,
    get_supported_formats_display,
    get_upload_limit_text,
)

__version__ = "1.0.0"

__all__ = [
    "ALLOWED_IMAGE_EXTENSIONS",
    "ALLOWED_MIME_TYPES",
    "DEFAULT_MODEL",
    "MAX_IMAGE_SIZE_MB",
    "MAX_TITLE_LENGTH",
    "OLLAMA_BASE_URL",
    "REQUEST_TIMEOUT",
    "get_supported_extensions",
    "get_supported_formats_display",
    "get_upload_limit_text",
]
