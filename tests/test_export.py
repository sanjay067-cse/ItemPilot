"""Tests for HTML and text export utilities in ItemPilot."""

import pytest
from itempilot.utils.export import build_export_html, build_export_txt


def test_build_export_html_structure_and_escaping():
    """Test that HTML export formats correctly and safely escapes HTML tags to prevent XSS."""
    title = 'Sony WH-1000XM4 <script>alert("hack")</script>'
    tagline = 'Great sound & comfort <img src=x onerror=alert(1)>'
    description = 'Authentic Sony headphones.\n\nFolds easily for storage.'
    features = ['Touch controls on earcup', 'Folding hinge for <convenience>']
    specifics = {
        'brand': 'Sony',
        'model': 'WH-1000XM4',
        'color': '<Black>',
        'unspecified': None,
    }

    html_out = build_export_html(
        title=title,
        description=description,
        features=features,
        specifics=specifics,
        tagline=tagline,
    )

    # Verify no raw unescaped script tags
    assert '<script>' not in html_out
    assert '&lt;script&gt;alert(&quot;hack&quot;)&lt;/script&gt;' in html_out

    # Verify image tag is escaped
    assert '<img src=x onerror=alert(1)>' not in html_out
    assert '&lt;img src=x onerror=alert(1)&gt;' in html_out

    # Verify specific value is escaped
    assert '&lt;Black&gt;' in html_out

    # Verify key sections exist
    assert 'Item Specifics' in html_out
    assert 'Key Highlights &amp; Benefits' in html_out or 'Key Highlights' in html_out
    assert 'Product Description' in html_out
    assert 'Sony WH-1000XM4' in html_out


def test_build_export_txt_structure():
    """Test plain text export generation."""
    title = 'Sony WH-1000XM4 Wireless Headphones'
    description = 'High quality headphones in good condition.'
    features = ['Touch controls', 'Carry case included']
    keywords = ['Sony', 'Headphones', 'Bluetooth']
    specifics = {'brand': 'Sony', 'color': 'Black'}
    missing = ['Verify original charger cord']

    txt_out = build_export_txt(
        title=title,
        description=description,
        features=features,
        keywords=keywords,
        specifics=specifics,
        missing_info=missing,
        tagline='Premium Audio',
    )

    assert 'TITLE (35/80 chars):' in txt_out
    assert 'SUBTITLE / TAGLINE (13/55 chars):' in txt_out
    assert 'Sony WH-1000XM4 Wireless Headphones' in txt_out
    assert '• Brand: Sony' in txt_out
    assert '[ ] Verify original charger cord' in txt_out


def test_package_exports_and_imports():
    """Verify that export and validation utilities are accessible from itempilot.utils directly."""
    from itempilot.utils import build_export_html as h1, build_export_txt as t1, validate_title_length as v1
    from itempilot.utils.export import build_export_html as h2, build_export_txt as t2
    from itempilot.utils.validation import validate_title_length as v2, build_export_html as h3

    assert h1 is h2
    assert t1 is t2
    assert v1 is v2
    assert h1 is h3


def test_html_export_excludes_seller_verification_notes():
    """Verify that HTML export is buyer-facing only and does not contain seller verification notes."""
    html_out = build_export_html(
        title="Nike Air Jordan 1",
        description="Classic retro sneakers.",
        features=["Durable rubber sole"],
        specifics={"brand": "Nike", "condition": "Used - Good"},
        tagline="Iconic High Top",
    )
    # Ensure no internal/checklist wording appears in buyer HTML
    assert "missing_info" not in html_out.lower()
    assert "verification checklist" not in html_out.lower()
    assert "seller-only" not in html_out.lower()
    assert "Nike Air Jordan 1" in html_out

