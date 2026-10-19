"""Tests for validation and parsing utilities in ItemPilot."""

import pytest

from itempilot.utils.validation import (
    detect_missing_fields,
    enforce_title_length,
    extract_json_from_text,
    parse_and_clean_json,
    validate_title_length,
)


def test_enforce_title_length_short():
    """Short titles remain unchanged."""
    title = "Vintage Nike Air Jordan 1 High Chicago Red 1985"
    assert enforce_title_length(title, 80) == title


def test_enforce_title_length_exact():
    """Titles at exactly 80 characters remain untouched."""
    title = "A" * 80
    assert enforce_title_length(title, 80) == title


def test_enforce_title_length_truncation():
    """Long titles are truncated to 80 chars max without cutting off awkward single letters."""
    long_title = (
        "Vintage Nike Air Jordan 1 High Chicago 1985 Original Red White Black "
        "Collectible Rare Retro Sneaker Sz 10.5 Excellent Condition"
    )
    result = enforce_title_length(long_title, 80)
    assert len(result) <= 80
    # Should end at a complete word boundary
    assert not result.endswith(" ")


def test_validate_title_length():
    """Test validation of title length function."""
    valid, err = validate_title_length("Apple iPhone 13 Pro 128GB Graphite Unlocked")
    assert valid is True
    assert err is None

    empty_valid, empty_err = validate_title_length("   ")
    assert empty_valid is False
    assert "cannot be empty" in (empty_err or "")

    overlong = "X" * 85
    over_valid, over_err = validate_title_length(overlong)
    assert over_valid is False
    assert "exceeding the 80-character" in (over_err or "")


def test_detect_missing_fields():
    """Test missing field detection from item specifics dictionary."""
    specifics = {
        "brand": "Apple",
        "model": "iPhone 13",
        "color": None,
        "condition": "",
        # "material" and "size" omitted entirely
    }
    missing = detect_missing_fields(specifics, recommended_keys=["brand", "model", "color", "condition", "material", "size"])
    assert "color" in missing
    assert "condition" in missing
    assert "material" in missing
    assert "size" in missing
    assert "brand" not in missing
    assert "model" not in missing


def test_extract_json_from_markdown():
    """Test extracting JSON wrapped in markdown code blocks."""
    raw = """Here is your listing:
```json
{
  "title": "Vintage Casio F-91W Watch",
  "description": "Classic digital watch in working condition.",
  "features": ["Water resistant", "Alarm"],
  "keywords": ["casio", "retro"],
  "item_specifics": {"brand": "Casio"},
  "missing_info": []
}
```
Hope this helps!"""
    parsed = parse_and_clean_json(raw)
    assert parsed["title"] == "Vintage Casio F-91W Watch"
    assert parsed["features"] == ["Water resistant", "Alarm"]


def test_extract_json_from_embedded_text():
    """Test extracting JSON without markdown fences."""
    raw = 'Sure thing! {"title": "Test Watch", "description": "Good", "features": [], "keywords": [], "item_specifics": {}, "missing_info": []} Enjoy!'
    parsed = parse_and_clean_json(raw)
    assert parsed["title"] == "Test Watch"


def test_parse_invalid_json_raises():
    """Test that malformed text without JSON raises ValueError."""
    with pytest.raises(ValueError):
        parse_and_clean_json("Sorry, I cannot analyze this image.")
