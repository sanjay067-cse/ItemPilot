"""Tests for configuration settings and upload limit formatting."""

import pytest
from unittest.mock import patch
from itempilot.config import (
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_IMAGE_SIZE_MB,
    get_supported_formats_display,
    get_upload_limit_text,
)


def test_get_supported_formats_display():
    """Verify that allowed extensions format to clean uppercase string without duplicates."""
    display = get_supported_formats_display()
    assert "JPG" in display
    assert "PNG" in display
    assert "WEBP" in display
    # Verify no leading dots or duplicates like JPEG and JPG together
    assert "." not in display
    assert "JPEG" not in display


def test_get_upload_limit_text_default():
    """Verify exact return value format for default 10 MB configuration."""
    limit_text = get_upload_limit_text()
    assert isinstance(limit_text, str)
    assert limit_text == "Up to 10 MB per file · JPG, PNG, WEBP"


def test_get_upload_limit_text_dynamic():
    """Verify that changing MAX_IMAGE_SIZE_MB dynamically changes the output."""
    with patch("itempilot.config.MAX_IMAGE_SIZE_MB", 25.0):
        assert get_upload_limit_text() == "Up to 25 MB per file · JPG, PNG, WEBP"

    with patch("itempilot.config.MAX_IMAGE_SIZE_MB", 5):
        assert get_upload_limit_text() == "Up to 5 MB per file · JPG, PNG, WEBP"


def test_import_from_package_root():
    """Verify that get_upload_limit_text and get_supported_extensions are also accessible from package root."""
    from itempilot import (
        get_supported_extensions as root_exts_func,
        get_upload_limit_text as root_func,
    )
    assert root_func() == "Up to 10 MB per file · JPG, PNG, WEBP"
    assert root_exts_func() == ["jpeg", "jpg", "png", "webp"]


def test_get_supported_extensions_format():
    """Verify get_supported_extensions returns sorted clean list without dots."""
    from itempilot.config import get_supported_extensions
    exts = get_supported_extensions()
    assert isinstance(exts, list)
    assert exts == ["jpeg", "jpg", "png", "webp"]
    assert all(not ext.startswith(".") for ext in exts)


def test_app_module_imports_cleanly():
    """Verify that app module imports without any ImportError or AttributeError."""
    import app
    assert callable(app.get_upload_limit_text)
    assert app.get_upload_limit_text() == "Up to 10 MB per file · JPG, PNG, WEBP"
    assert callable(app.get_supported_extensions)
    assert app.get_supported_extensions() == ["jpeg", "jpg", "png", "webp"]
    assert callable(app.ImageService.get_supported_extensions)
    assert app.ImageService.get_supported_extensions() == ["jpeg", "jpg", "png", "webp"]

