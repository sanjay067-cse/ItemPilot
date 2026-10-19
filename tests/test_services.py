"""Tests for ImageService, OllamaService, and ListingService."""

import io
from unittest.mock import MagicMock
from PIL import Image
import pytest

from itempilot.schemas import SellerInput
from itempilot.services.image_service import ImageService, ImageValidationError
from itempilot.services.listing_service import ListingService, ListingServiceError
from itempilot.services.ollama_service import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaService,
)


@pytest.fixture
def sample_png_bytes() -> bytes:
    """Generate in-memory valid PNG image bytes for testing."""
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    """Generate in-memory valid JPEG image bytes for testing."""
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_image_service_valid_png(sample_png_bytes):
    """Test valid PNG byte stream validation."""
    valid, err = ImageService.validate_image_file(sample_png_bytes, filename="test.png")
    assert valid is True
    assert err is None


def test_image_service_valid_jpeg(sample_jpeg_bytes):
    """Test valid JPEG byte stream validation."""
    valid, err = ImageService.validate_image_file(sample_jpeg_bytes, filename="item.jpg")
    assert valid is True
    assert err is None


def test_image_service_empty_bytes():
    """Test empty image bytes validation failure."""
    valid, err = ImageService.validate_image_file(b"")
    assert valid is False
    assert "empty" in (err or "").lower()


def test_image_service_unsupported_extension(sample_png_bytes):
    """Test rejection of unsupported file extensions."""
    valid, err = ImageService.validate_image_file(sample_png_bytes, filename="test.bmp")
    assert valid is False
    assert "unsupported file extension" in (err or "").lower()


def test_image_service_corrupted_file():
    """Test rejection of corrupted image bytes."""
    corrupted = b"PK\x03\x04not-an-image-file-header"
    valid, err = ImageService.validate_image_file(corrupted, filename="test.png")
    assert valid is False
    assert "invalid or corrupted" in (err or "").lower()


def test_image_service_base64_encoding(sample_png_bytes):
    """Test base64 encoding returns non-empty string."""
    b64 = ImageService.encode_to_base64(sample_png_bytes)
    assert isinstance(b64, str)
    assert len(b64) > 0


def test_dynamic_upload_limit_text():
    """Verify that upload limit text is generated dynamically from configuration."""
    from itempilot.config import get_upload_limit_text
    limit_text = get_upload_limit_text()
    assert limit_text == "Up to 10 MB per file · JPG, PNG, WEBP"
    assert ImageService.get_upload_limit_text() == "Up to 10 MB per file · JPG, PNG, WEBP"
    assert ImageService.get_supported_extensions() == ["jpeg", "jpg", "png", "webp"]


def test_image_service_exceeds_configured_size():
    """Test that files exceeding configured max size (10 MB) are rejected."""
    # 11 MB of dummy bytes
    oversized_bytes = b"x" * int(11 * 1024 * 1024)
    valid, err = ImageService.validate_image_file(oversized_bytes, filename="huge.jpg")
    assert valid is False
    assert "exceeds maximum allowed limit" in (err or "").lower()
    assert "10.0 mb" in (err or "").lower()


def test_listing_service_success(sample_png_bytes):
    """Test full generation flow with a mocked successful Ollama call."""
    mock_ollama = MagicMock(spec=OllamaService)
    mock_ollama.generate.return_value = """
    {
      "title": "Nike Air Max 90 Running Shoes Mens Size 10 Black White - Good Condition",
      "description": "Authentic Nike Air Max 90 sneakers in good pre-owned condition. Clean uppers with light tread wear.",
      "features": ["Classic Air Max cushioning", "Durable leather and mesh upper", "Waffle outsole"],
      "keywords": ["Nike", "Air Max 90", "Running Shoes", "Sneakers", "Size 10"],
      "item_specifics": {
        "brand": "Nike",
        "model": "Air Max 90",
        "color": "Black/White",
        "condition": "Used",
        "material": "Leather/Mesh",
        "size": "10"
      },
      "missing_info": ["Original box not visible in image."]
    }
    """

    service = ListingService(ollama_service=mock_ollama)
    seller_input = SellerInput(brand="Nike", condition="Used - Good")

    result = service.generate_listing(
        image_bytes=sample_png_bytes,
        filename="shoes.png",
        seller_input=seller_input,
    )

    assert result.title.startswith("Nike Air Max 90")
    assert len(result.title) <= 80
    assert result.item_specifics["brand"] == "Nike"
    assert len(result.features) == 3
    assert mock_ollama.generate.call_count == 1


def test_listing_service_passes_writing_style_to_prompt(sample_png_bytes):
    """Test that seller-selected writing style is included in the prompt."""
    mock_ollama = MagicMock(spec=OllamaService)
    mock_ollama.generate.return_value = """{
        "title": "Vintage Casio F-91W Digital Watch Black Resin - Clean",
        "description": "Iconic retro digital watch.",
        "features": ["Water resistant", "Alarm"],
        "keywords": ["Casio", "Retro"],
        "item_specifics": {"brand": "Casio"},
        "missing_info": []
    }"""
    service = ListingService(ollama_service=mock_ollama)
    seller_input = SellerInput(brand="Casio", writing_style="Benefit-focused")
    service.generate_listing(image_bytes=sample_png_bytes, seller_input=seller_input)
    prompt_sent = mock_ollama.generate.call_args[1]["prompt"]
    assert "Benefit-focused" in prompt_sent


def test_listing_service_retry_on_initial_bad_json(sample_png_bytes):
    """Test that listing service retries once if first response is invalid JSON."""
    mock_ollama = MagicMock(spec=OllamaService)
    # First attempt fails with malformed JSON, second attempt succeeds
    mock_ollama.generate.side_effect = [
        "Not valid JSON output here",
        """{
            "title": "Vintage Polaroid Sun 600 Instant Film Camera Black",
            "description": "Vintage Polaroid 600 instant camera in cosmetically sound condition.",
            "features": ["Built-in flash", "Takes 600 film"],
            "keywords": ["Polaroid", "Vintage Camera"],
            "item_specifics": {"brand": "Polaroid"},
            "missing_info": ["Film testing not verified."]
        }"""
    ]

    service = ListingService(ollama_service=mock_ollama)
    result = service.generate_listing(
        image_bytes=sample_png_bytes,
        filename="camera.png",
        allow_retry=True,
    )

    assert result.title == "Vintage Polaroid Sun 600 Instant Film Camera Black"
    assert mock_ollama.generate.call_count == 2


def test_listing_service_fails_after_retry(sample_png_bytes):
    """Test that listing service raises ListingServiceError if both attempts fail."""
    mock_ollama = MagicMock(spec=OllamaService)
    mock_ollama.generate.side_effect = [
        "Malformed attempt 1",
        "Malformed attempt 2",
    ]

    service = ListingService(ollama_service=mock_ollama)
    with pytest.raises(ListingServiceError):
        service.generate_listing(
            image_bytes=sample_png_bytes,
            filename="camera.png",
            allow_retry=True,
        )
    assert mock_ollama.generate.call_count == 2


def test_listing_service_invalid_image():
    """Test that invalid image fails fast before contacting Ollama."""
    mock_ollama = MagicMock(spec=OllamaService)
    service = ListingService(ollama_service=mock_ollama)

    with pytest.raises(ImageValidationError):
        service.generate_listing(
            image_bytes=b"not-an-image",
            filename="bad.jpg",
        )
    mock_ollama.generate.assert_not_called()
