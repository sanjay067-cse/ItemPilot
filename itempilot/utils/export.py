"""Export formatting utilities for ItemPilot listings (HTML and TXT)."""

import html
from typing import Any, Dict, List, Optional


def build_export_html(
    title: str,
    description: str,
    features: List[str],
    specifics: Dict[str, Any],
    tagline: Optional[str] = None,
) -> str:
    """Generate clean, mobile-responsive, eBay-compliant HTML for the item description.

    All user and model inputs are strictly escaped using html.escape to guarantee
    safe HTML export without XSS vulnerabilities.
    """
    safe_title = html.escape((title or "").strip())
    safe_tagline = html.escape((tagline or "").strip()) if tagline else ""

    # Format description paragraphs safely
    escaped_desc = html.escape((description or "").strip())
    paragraphs = [p.strip() for p in escaped_desc.split("\n\n") if p.strip()]
    if not paragraphs and escaped_desc:
        paragraphs = [escaped_desc]

    desc_html = "".join(
        f'<p style="margin: 0 0 14px 0; line-height: 1.6; color: #374151;">{p.replace(chr(10), "<br>")}</p>'
        for p in paragraphs
    )

    # Format feature bullets safely
    feature_items = "".join(
        f'<li style="margin-bottom: 8px; line-height: 1.5; color: #374151;">{html.escape(f.strip())}</li>'
        for f in features
        if f and f.strip()
    )

    # Format specifics safely into clean table rows
    spec_rows = ""
    for k, v in specifics.items():
        if v is not None and str(v).strip() and str(v).strip().lower() != "null":
            safe_k = html.escape(str(k).replace("_", " ").capitalize())
            safe_v = html.escape(str(v).strip())
            spec_rows += f"""
            <tr>
              <td style="padding: 9px 14px; background-color: #F9FAFB; border-bottom: 1px solid #E5E7EB; font-weight: 600; width: 35%; color: #4B5563;">{safe_k}</td>
              <td style="padding: 9px 14px; border-bottom: 1px solid #E5E7EB; color: #111827;">{safe_v}</td>
            </tr>"""

    # Assemble complete eBay listing HTML template
    tagline_block = f'<div style="font-size: 15px; color: #4B5563; margin-top: 4px; font-style: italic;">{safe_tagline}</div>' if safe_tagline else ""

    specifics_section = f"""
  <section style="margin-bottom: 24px;">
    <h2 style="font-size: 16px; font-weight: 700; color: #1E3A8A; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid #E5E7EB; padding-bottom: 6px; margin: 0 0 12px 0;">Item Specifics</h2>
    <table style="width: 100%; border-collapse: collapse; font-size: 14px; border: 1px solid #E5E7EB; border-radius: 4px; overflow: hidden;">
      <tbody>{spec_rows}
      </tbody>
    </table>
  </section>""" if spec_rows else ""

    features_section = f"""
  <section style="margin-bottom: 24px;">
    <h2 style="font-size: 16px; font-weight: 700; color: #1E3A8A; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid #E5E7EB; padding-bottom: 6px; margin: 0 0 12px 0;">Key Highlights & Benefits</h2>
    <ul style="padding-left: 22px; margin: 0; font-size: 14px;">
      {feature_items}
    </ul>
  </section>""" if feature_items else ""

    html_content = f"""<!-- ItemPilot eBay Listing Template -->
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 860px; margin: 0 auto; padding: 24px; border: 1px solid #E5E7EB; border-radius: 8px; background-color: #FFFFFF; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
  <header style="border-bottom: 2px solid #2563EB; padding-bottom: 16px; margin-bottom: 24px;">
    <h1 style="font-size: 22px; font-weight: 700; color: #111827; margin: 0; line-height: 1.3;">{safe_title}</h1>{tagline_block}
  </header>{specifics_section}{features_section}
  <section style="margin-bottom: 24px;">
    <h2 style="font-size: 16px; font-weight: 700; color: #1E3A8A; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid #E5E7EB; padding-bottom: 6px; margin: 0 0 12px 0;">Product Description</h2>
    <div style="font-size: 14px;">
      {desc_html}
    </div>
  </section>

  <footer style="margin-top: 32px; padding-top: 16px; border-top: 1px solid #E5E7EB; text-align: center; font-size: 13px; color: #6B7280;">
    Questions? Please reach out before purchasing—we are happy to provide additional details!
  </footer>
</div>
"""
    return html_content


def build_export_txt(
    title: str,
    description: str,
    features: List[str],
    keywords: List[str],
    specifics: Dict[str, Any],
    missing_info: List[str],
    tagline: Optional[str] = None,
) -> str:
    """Format full listing as a human-readable text file ready for eBay."""
    lines = [
        "==================================================================",
        "                    ITEMPILOT EBAY LISTING EXPORT                 ",
        "==================================================================",
        "",
        f"TITLE ({len(title)}/80 chars):",
        title,
    ]
    if tagline:
        lines.extend([
            "",
            f"SUBTITLE / TAGLINE ({len(tagline)}/55 chars):",
            tagline,
        ])
    lines.extend([
        "",
        "ITEM SPECIFICS:",
    ])
    for k, v in specifics.items():
        if v is not None and str(v).strip() and str(v).strip().lower() != "null":
            lines.append(f"  • {k.capitalize()}: {v}")

    lines.extend([
        "",
        "KEY FEATURES & BENEFITS:",
    ])
    for f in features:
        lines.append(f"  • {f}")

    lines.extend([
        "",
        "SEARCH KEYWORDS & TAGS:",
        ", ".join(keywords),
        "",
        "ITEM DESCRIPTION:",
        description,
        "",
        "PRE-LISTING VERIFICATION CHECKLIST (MISSING INFO):",
    ])
    if missing_info:
        for m in missing_info:
            lines.append(f"  [ ] {m}")
    else:
        lines.append("  [x] All essential item specifics verified!")

    lines.append("")
    lines.append("Generated with ItemPilot (Local AI via Gemma 3 & Ollama)")
    return "\n".join(lines)
