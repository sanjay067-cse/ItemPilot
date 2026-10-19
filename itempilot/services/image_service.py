"""Image validation and processing service for ItemPilot."""

import base64
import io
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image

from itempilot.config import (
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_IMAGE_SIZE_MB,
    get_supported_extensions,
    get_upload_limit_text,
)


class ImageValidationError(Exception):
    """Raised when an uploaded image fails validation."""
    pass


class ImageService:
    """Handles image validation, encoding, and preparation for multimodal models."""

    @classmethod
    def get_upload_limit_text(cls) -> str:
        """Get formatted dynamic limit text e.g. 'Up to 10 MB per file · JPG, PNG, WEBP'."""
        return get_upload_limit_text()

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """Get list of extensions without leading dot for file uploaders."""
        return get_supported_extensions()

    @staticmethod
    def validate_image_file(
        image_bytes: bytes,
        filename: Optional[str] = None,
        max_size_mb: float = MAX_IMAGE_SIZE_MB
    ) -> Tuple[bool, Optional[str]]:
        """Validate image bytes for size, extension, and integrity.

        Returns (is_valid, error_message).
        """
        if not image_bytes or len(image_bytes) == 0:
            return False, "Image file is empty."

        # Check file size
        size_mb = len(image_bytes) / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"File size ({size_mb:.1f} MB) exceeds maximum allowed limit ({max_size_mb:.1f} MB)."

        # Check extension if filename provided
        if filename:
            ext = Path(filename).suffix.lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                allowed_str = ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))
                return False, f"Unsupported file extension '{ext}'. Allowed: {allowed_str}"

        # Verify integrity using PIL
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
                fmt = (img.format or "").upper()
                if fmt not in {"JPEG", "PNG", "WEBP"}:
                    return False, f"Unsupported image format '{fmt}'. Must be JPEG, PNG, or WEBP."
        except Exception as e:
            return False, f"Invalid or corrupted image: {str(e)}"

        return True, None

    @staticmethod
    def encode_to_base64(image_bytes: bytes) -> str:
        """Encode raw image bytes into base64 string for Ollama vision API."""
        return base64.b64encode(image_bytes).decode("utf-8")

    @staticmethod
    def get_pil_image(image_bytes: bytes) -> Image.Image:
        """Open raw image bytes into a PIL Image."""
        return Image.open(io.BytesIO(image_bytes))
