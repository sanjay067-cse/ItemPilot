"""Tests for Pydantic data schemas in ItemPilot."""

import pytest
from pydantic import ValidationError

from itempilot.schemas import ListingOutput, SellerInput


def test_seller_input_valid():
    """Test SellerInput schema with full and partial fields."""
    full = SellerInput(
        category="Electronics",
        brand="Sony",
        model_sku="WH-1000XM4",
        condition="Used - Excellent",
        color="Black",
        material="Plastic",
        size_dimensions="Over-ear",
        features="Noise cancelling, carrying case included",
    )
    assert full.brand == "Sony"
    assert full.model_sku == "WH-1000XM4"

    empty = SellerInput()
    assert empty.brand is None
    assert empty.condition is None


def test_listing_output_valid():
    """Test that ListingOutput accepts valid data within constraints."""
    data = {
        "title": "Sony WH-1000XM4 Wireless Noise Canceling Headphones Black - Excellent",
        "description": "Authentic Sony WH-1000XM4 wireless headphones in excellent condition.",
        "features": [
            "Industry-leading active noise cancellation",
            "Touch sensor controls and 30-hour battery life",
        ],
        "keywords": ["Sony", "WH-1000XM4", "Noise Canceling", "Bluetooth"],
        "item_specifics": {
            "brand": "Sony",
            "model": "WH-1000XM4",
            "color": "Black",
            "condition": "Used",
        },
        "missing_info": [
            "Original charging cable inclusion not verified in photo."
        ],
    }

    listing = ListingOutput(**data)
    assert listing.title == data["title"]
    assert len(listing.title) <= 80
    assert len(listing.features) == 2
    assert listing.item_specifics["brand"] == "Sony"
    assert listing.promotional_tagline is None

    # Test with promotional_tagline provided
    data_with_tagline = dict(data, promotional_tagline="Premium Sound with Extra Case")
    listing2 = ListingOutput(**data_with_tagline)
    assert listing2.promotional_tagline == "Premium Sound with Extra Case"


def test_listing_output_rejects_empty_title():
    """Test that ListingOutput rejects blank or empty titles."""
    with pytest.raises(ValidationError) as exc_info:
        ListingOutput(
            title="   ",
            description="Valid description",
            features=[],
            keywords=[],
            item_specifics={},
            missing_info=[],
        )
    assert "Listing title cannot be empty" in str(exc_info.value)


def test_listing_output_rejects_overlong_title():
    """Test that ListingOutput rejects titles exceeding 80 characters."""
    long_title = "Sony WH-1000XM4 Wireless Noise Cancelling Over-Ear Headphones Black with Extra Cable and Pouch Accessories Included"
    assert len(long_title) > 80

    with pytest.raises(ValidationError) as exc_info:
        ListingOutput(
            title=long_title,
            description="Valid description",
            features=[],
            keywords=[],
            item_specifics={},
            missing_info=[],
        )
    assert "exceeds 80 characters" in str(exc_info.value) or "at most 80 characters" in str(exc_info.value)


def test_listing_output_rejects_missing_required_fields():
    """Test that ListingOutput fails when required fields are missing."""
    with pytest.raises(ValidationError):
        # Missing description
        ListingOutput(
            title="Valid Short Title",  # type: ignore
        )
