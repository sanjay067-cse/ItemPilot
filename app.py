"""ItemPilot - Local AI eBay Listing Assistant.

A modern, productivity-focused application for analyzing product images and
generating structured, buyer-oriented, hallucination-guarded eBay listings using
local Gemma 3 models via Ollama.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure application root directory is prioritized in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Guarantee clean module loading even if running in a long-lived Streamlit server
import importlib
import itempilot.config
if not hasattr(itempilot.config, "get_upload_limit_text") or not hasattr(itempilot.config, "get_supported_extensions"):
    importlib.reload(itempilot.config)

import itempilot.services.image_service
if not hasattr(itempilot.services.image_service.ImageService, "get_supported_extensions"):
    importlib.reload(itempilot.services.image_service)

import streamlit as st
from PIL import Image

from itempilot.config import (
    ALLOWED_IMAGE_EXTENSIONS,
    DEFAULT_MODEL,
    MAX_IMAGE_SIZE_MB,
    MAX_TITLE_LENGTH,
    OLLAMA_BASE_URL,
    get_supported_extensions,
    get_upload_limit_text,
)
from itempilot.schemas import ListingOutput, SellerInput
from itempilot.services.image_service import ImageService, ImageValidationError
from itempilot.services.listing_service import ListingService, ListingServiceError
from itempilot.services.ollama_service import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaService,
)
from itempilot.utils.export import build_export_html, build_export_txt
from itempilot.utils.validation import validate_title_length

# Configure page layout and meta
st.set_page_config(
    page_title="ItemPilot — Local AI eBay Listing Assistant",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional SaaS Custom CSS Styling
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2.5rem;
            max-width: 1320px;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #0F172A;
            font-weight: 600;
            letter-spacing: -0.015em;
        }

        .ip-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }

        .ip-card-header {
            font-size: 0.95rem;
            font-weight: 600;
            color: #1E293B;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .ip-step-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.75rem;
            margin: 1rem 0;
        }

        .ip-step {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 0.85rem;
        }

        .ip-step-num {
            font-size: 0.75rem;
            font-weight: 700;
            color: #2563EB;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }

        .ip-step-title {
            font-size: 0.88rem;
            font-weight: 600;
            color: #0F172A;
            margin-bottom: 0.2rem;
        }

        .ip-step-desc {
            font-size: 0.78rem;
            color: #64748B;
            line-height: 1.35;
        }

        .ip-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.25rem 0.65rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        .ip-badge-success {
            background-color: #F0FDF4;
            color: #166534;
            border: 1px solid #BBF7D0;
        }
        .ip-badge-warning {
            background-color: #FFFBEB;
            color: #92400E;
            border: 1px solid #FDE68A;
        }
        .ip-badge-danger {
            background-color: #FEF2F2;
            color: #991B1B;
            border: 1px solid #FECACA;
        }

        .ip-example-box {
            background: #FFFFFF;
            border: 1px dashed #CBD5E1;
            border-radius: 8px;
            padding: 1.15rem;
            margin-top: 1rem;
        }

        .ip-char-counter {
            font-size: 0.8rem;
            font-weight: 500;
            margin-top: 0.25rem;
            display: flex;
            justify-content: space-between;
        }
        .ip-char-ok {
            color: #2563EB;
        }
        .ip-char-warn {
            color: #DC2626;
            font-weight: 600;
        }

        .stTextInput > label, .stTextArea > label, .stSelectbox > label {
            font-size: 0.84rem !important;
            font-weight: 500 !important;
            color: #334155 !important;
        }

        .stButton > button {
            border-radius: 6px;
            font-weight: 500;
        }

        /* Marketplace Preview Styling */
        .ip-marketplace-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }
        .ip-preview-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #0F172A;
            line-height: 1.35;
            margin-bottom: 0.35rem;
        }
        .ip-preview-tagline {
            font-size: 0.9rem;
            font-style: italic;
            color: #475569;
            margin-bottom: 0.75rem;
        }
        .ip-section-title {
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #1E3A8A;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 0.3rem;
            margin-top: 1rem;
            margin-bottom: 0.6rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=25, show_spinner=False)
def get_cached_ollama_status(base_url: str, model_name: str) -> Dict[str, Any]:
    """Check Ollama service and model availability, cached for 25 seconds to prevent lag."""
    ollama_svc = OllamaService(base_url=base_url, model=model_name)
    return ollama_svc.get_service_status()


def get_listing_service(base_url: str, model_name: str) -> ListingService:
    """Initialize listing service with specified Ollama host and model."""
    ollama = OllamaService(base_url=base_url, model=model_name)
    return ListingService(ollama_service=ollama)


def render_onboarding_empty_state():
    """Render a structured, clean onboarding empty state when no listing has been generated."""
    st.markdown(
        """
        <div class="ip-card">
            <div class="ip-card-header">
                <span>How ItemPilot Works</span>
            </div>
            <p style="font-size: 0.88rem; color: #475569; margin-bottom: 0.5rem; line-height: 1.5;">
                ItemPilot thinks like a professional e-commerce copywriter. Using <strong>Gemma 3 4B</strong> running locally via <strong>Ollama</strong>, 
                it identifies visible features, turns confirmed specs into practical buyer benefits, and writes persuasive eBay listings that build buyer confidence.
            </p>
            <div class="ip-step-container">
                <div class="ip-step">
                    <div class="ip-step-num">Step 1</div>
                    <div class="ip-step-title">Upload Photo</div>
                    <div class="ip-step-desc">Provide a clear shot showing logos, model markings, ports, or condition.</div>
                </div>
                <div class="ip-step">
                    <div class="ip-step-num">Step 2</div>
                    <div class="ip-step-title">Add Known Details</div>
                    <div class="ip-step-desc">Enter brand, model, inclusions, or flaws (all fields are optional).</div>
                </div>
                <div class="ip-step">
                    <div class="ip-step-num">Step 3</div>
                    <div class="ip-step-title">Generate & Review</div>
                    <div class="ip-step-desc">Inspect the buyer-facing preview, review the seller checklist, and export.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Example Preview Box
    st.markdown(
        """
        <div class="ip-example-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                <span style="font-size: 0.75rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">
                    Sample Preview — Example Output Only
                </span>
                <span class="ip-badge ip-badge-success" style="font-size: 0.72rem;">Demonstration</span>
            </div>
            <div style="margin-bottom: 0.6rem;">
                <span style="font-size: 0.8rem; font-weight: 600; color: #334155;">Example Title:</span>
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 4px; padding: 0.45rem 0.65rem; font-size: 0.85rem; font-weight: 500; color: #0F172A; margin-top: 0.2rem;">
                    Sony WH-1000XM4 Wireless Noise Canceling Headphones Black - Tested Working
                </div>
                <div style="font-size: 0.74rem; color: #64748B; margin-top: 0.2rem;">74 / 80 characters used (6 remaining)</div>
            </div>
            <div style="margin-bottom: 0.6rem;">
                <span style="font-size: 0.8rem; font-weight: 600; color: #334155;">Example Highlights:</span>
                <ul style="font-size: 0.8rem; color: #334155; margin: 0.2rem 0; padding-left: 1.2rem;">
                    <li><strong>Intuitive Touch Sensor Controls:</strong> Quickly adjust volume or skip tracks without reaching for your device.</li>
                    <li><strong>Compact Folding Earcups:</strong> Swivels flat for easy packing in bags during daily commutes.</li>
                </ul>
            </div>
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 4px; padding: 0.5rem 0.75rem; font-size: 0.78rem; color: #92400E; margin-bottom: 0.5rem;">
                <strong>Seller Checklist Note:</strong> Verify whether original 3.5mm audio cord and USB-C cable are included in shipment.
            </div>
            <p style="font-size: 0.76rem; color: #94A3B8; margin: 0; font-style: italic;">
                Your generated listing draft will appear here once you upload an image and click "Generate eBay Listing".
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def execute_generation(
    ollama_url: str,
    model_name: str,
    seller_ctx: SellerInput,
):
    """Execute listing generation through ListingService and store in session state."""
    listing_service = get_listing_service(base_url=ollama_url, model_name=model_name)

    with st.spinner("Analyzing your product photo and preparing your listing..."):
        try:
            result = listing_service.generate_listing(
                image_bytes=st.session_state.image_bytes,
                filename=st.session_state.image_name,
                seller_input=seller_ctx,
                allow_retry=True,
            )
            st.session_state.listing_data = result.model_dump()
            st.session_state.active_seller_input = seller_ctx.model_dump()
            st.toast("Listing generated successfully!", icon="✅")
            st.rerun()
        except OllamaConnectionError as e:
            st.error(f"Connection failed: {str(e)}")
        except OllamaModelNotFoundError as e:
            st.error(f"Model missing: {str(e)}")
        except ImageValidationError as e:
            st.error(f"Image error: {str(e)}")
        except ListingServiceError as e:
            st.error(f"Generation error: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")


def main():
    # Header bar
    col_head_title, col_head_badge = st.columns([3, 1])
    with col_head_title:
        st.title("ItemPilot")
        st.caption("Local AI eBay Listing Assistant — Powered by Gemma 3 & Ollama")

    # Sidebar: Model Configuration and Local Processing Architecture
    with st.sidebar:
        st.markdown("### Local AI Engine")
        ollama_url = st.text_input(
            "Ollama Base URL",
            value=OLLAMA_BASE_URL,
            help="Address of your local Ollama instance (default: http://localhost:11434)"
        )
        model_name = st.text_input(
            "Target Vision Model",
            value=DEFAULT_MODEL,
            help="Local multimodal model name (default: gemma3:4b)"
        )

        # Cached connection check
        status = get_cached_ollama_status(base_url=ollama_url, model_name=model_name)

        if not status["reachable"]:
            st.error("Ollama Offline")
            st.caption(
                "Cannot connect to the Ollama server at the configured address.\n\n"
                "Start Ollama locally from your terminal:\n"
                "```bash\nollama serve\n```"
            )
        elif not status["model_available"]:
            st.warning(f"Model Missing: `{model_name}`")
            st.caption(
                f"Ollama is reachable, but the model `{model_name}` is not installed.\n\n"
                f"Install it from your terminal:\n```bash\nollama pull {model_name}\n```"
            )
            if status["installed_models"]:
                st.caption("Installed models: " + ", ".join(f"`{m}`" for m in status["installed_models"]))
        else:
            st.success(f"Ollama Online · `{model_name}`")

        if st.button("Check Connection", use_container_width=True, help="Refresh Ollama status"):
            get_cached_ollama_status.clear()
            st.rerun()

        st.divider()

        st.markdown("### Local Processing")
        st.caption(
            "Inference runs locally through your Ollama instance. Images and details "
            "are processed on your machine and are not sent to third-party cloud AI APIs."
        )

        st.markdown("### Hallucination Guardrails")
        st.caption(
            "The model is instructed to describe strictly visible attributes and seller-supplied context. "
            "Unverified specifications are flagged in Missing Information for your confirmation before publishing."
        )

    # Header status pill
    with col_head_badge:
        if status["reachable"] and status["model_available"]:
            st.markdown(
                '<div style="text-align: right; padding-top: 1rem;">'
                '<span class="ip-badge ip-badge-success">● Ollama Connected</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        elif status["reachable"]:
            st.markdown(
                '<div style="text-align: right; padding-top: 1rem;">'
                '<span class="ip-badge ip-badge-warning">● Model Missing</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="text-align: right; padding-top: 1rem;">'
                '<span class="ip-badge ip-badge-danger">● Ollama Offline</span>'
                '</div>',
                unsafe_allow_html=True,
            )

    # Initialize session state for listing data and form state
    if "listing_data" not in st.session_state:
        st.session_state.listing_data = None
    if "image_bytes" not in st.session_state:
        st.session_state.image_bytes = None
    if "image_name" not in st.session_state:
        st.session_state.image_name = None
    if "active_seller_input" not in st.session_state:
        st.session_state.active_seller_input = None

    # Main 2-Column Interface
    col_input, col_output = st.columns([1, 1], gap="large")

    # ----------------------------------------------------
    # LEFT PANEL: Input & Upload Form
    # ----------------------------------------------------
    with col_input:
        st.subheader("1. Product Photos & Details")

        # Format label and limit text dynamically aligned with actual configuration
        upload_limit_text = get_upload_limit_text()
        upload_label = f"Upload Product Photo ({upload_limit_text})"
        
        # Supported extensions derived from ImageService with fallback to config
        supported_exts = (
            ImageService.get_supported_extensions()
            if hasattr(ImageService, "get_supported_extensions")
            else get_supported_extensions()
        )

        # Image uploader kept OUTSIDE the form so uploading updates preview immediately
        uploaded_file = st.file_uploader(
            upload_label,
            type=supported_exts,
            key="product_photo_uploader",
            help=f"{upload_limit_text}. High-quality photo showing the item, labels, markings, and physical condition. Processed in-memory."
        )
        st.caption(f"**{upload_limit_text}**")

        if uploaded_file is not None:
            raw_bytes = uploaded_file.getvalue()
            is_valid, err_msg = ImageService.validate_image_file(raw_bytes, filename=uploaded_file.name)
            if not is_valid:
                st.error(f"Image error: {err_msg}")
            else:
                st.session_state.image_bytes = raw_bytes
                st.session_state.image_name = uploaded_file.name

        if st.session_state.image_bytes is not None:
            st.image(
                st.session_state.image_bytes,
                caption=f"Selected: {st.session_state.image_name or 'Product Photo'}",
                use_container_width=True,
            )

        # Seller Details enclosed in an st.form to prevent reruns while typing
        with st.form("seller_details_form", clear_on_submit=False):
            st.markdown("##### Optional Seller Context")
            st.caption("Provide known details to guide the AI. All fields below are optional.")

            cat_input = st.text_input(
                "Category / Product Type",
                placeholder="e.g. Wireless Noise Canceling Headphones, Mechanical Keyboard",
                help="Helps the model classify the item into standard eBay categories."
            )

            b_col1, b_col2 = st.columns(2)
            with b_col1:
                brand_input = st.text_input("Brand", placeholder="e.g. Sony, Apple, Bose")
                color_input = st.text_input("Color", placeholder="e.g. Matte Black")
                material_input = st.text_input("Material", placeholder="e.g. Aluminum, Leather")
            with b_col2:
                sku_input = st.text_input("Model / MPN / SKU", placeholder="e.g. WH-1000XM4")
                
                condition_options = [
                    "Select condition (optional)...",
                    "Brand New / Sealed",
                    "Open Box / Like New",
                    "Used - Excellent (minimal wear)",
                    "Used - Good (normal wear)",
                    "Used - Acceptable (noticeable wear)",
                    "For Parts or Not Working",
                ]
                condition_choice = st.selectbox(
                    "Item Condition",
                    options=condition_options,
                    index=0,
                    help="Neutral by default. If unselected, the model will assess condition visually and flag it in verification."
                )
                size_input = st.text_input("Size / Dimensions", placeholder="e.g. Over-Ear, 10.5 US, 12x8 in")

            features_input = st.text_area(
                "Known Features, Inclusions & Flaws",
                placeholder="e.g. Fully tested working, includes original carry case and audio cable. Minor cosmetic scuff on left hinge.",
                height=80,
                help="Accurately listing cosmetic flaws or missing accessories prevents post-sale buyer disputes."
            )

            # Copywriting style selector
            style_options = ["Clear and informative", "Benefit-focused", "Concise"]
            selected_style = st.selectbox(
                "Listing Copy Style",
                options=style_options,
                index=0,
                help="Tailors how confirmed features are presented (practical utility vs concise scannability) while maintaining strict factual accuracy."
            )

            # Form submit button prevents premature reruns and AI inference
            generate_clicked = st.form_submit_button(
                "Generate eBay Listing",
                type="primary",
                use_container_width=True,
            )

        # Helper note when image is not yet chosen
        if st.session_state.image_bytes is None:
            st.caption("Upload a product photo above to enable listing generation.")

        # Process form submission
        if generate_clicked:
            if not st.session_state.image_bytes:
                st.warning("Please upload a product photo above before generating a listing.")
            else:
                selected_condition = condition_choice if condition_choice != "Select condition (optional)..." else None

                seller_ctx = SellerInput(
                    category=cat_input.strip() or None,
                    brand=brand_input.strip() or None,
                    model_sku=sku_input.strip() or None,
                    condition=selected_condition,
                    color=color_input.strip() or None,
                    material=material_input.strip() or None,
                    size_dimensions=size_input.strip() or None,
                    features=features_input.strip() or None,
                    writing_style=selected_style,
                )

                execute_generation(
                    ollama_url=ollama_url,
                    model_name=model_name,
                    seller_ctx=seller_ctx,
                )

    # ----------------------------------------------------
    # RIGHT PANEL: Generated Results or Onboarding State
    # ----------------------------------------------------
    with col_output:
        st.subheader("2. Generated Listing & Verification")

        if not st.session_state.listing_data:
            render_onboarding_empty_state()
        else:
            listing = st.session_state.listing_data

            # Top Control Bar: Draft Banner & Quick Actions
            st.markdown(
                """
                <div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-left: 4px solid #2563EB; border-radius: 4px; padding: 0.65rem 0.9rem; margin-bottom: 0.85rem;">
                    <div style="font-weight: 600; color: #1E293B; font-size: 0.86rem;">Listing Draft for Review</div>
                    <div style="font-size: 0.78rem; color: #475569; margin-top: 0.15rem;">
                        Generated by local AI. Please verify specifications, cosmetic condition, and included accessories against your physical item before publishing to eBay.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Regeneration and Reset Controls
            c_regen, c_reset = st.columns([1, 1])
            with c_regen:
                if st.button("🔄 Regenerate Copy", use_container_width=True, help="Re-run the listing generation with current inputs"):
                    if st.session_state.image_bytes:
                        active_dict = st.session_state.get("active_seller_input") or {}
                        seller_ctx = SellerInput(**active_dict)
                        execute_generation(
                            ollama_url=ollama_url,
                            model_name=model_name,
                            seller_ctx=seller_ctx,
                        )
                    else:
                        st.warning("Please upload an image first.")
            with c_reset:
                if st.button("Clear / New Listing", use_container_width=True):
                    st.session_state.listing_data = None
                    st.session_state.image_bytes = None
                    st.session_state.image_name = None
                    st.rerun()

            # Presentation Tabs: Marketplace Preview, Edit Fields, Export & Copy
            tab_preview, tab_edit, tab_export = st.tabs([
                "Listing Preview",
                "Edit Fields",
                "Export & Copy",
            ])

            # Retrieve active values from session state if already edited, or defaults from listing
            cur_title = st.session_state.get("edit_title", listing.get("title", ""))
            cur_tagline = st.session_state.get("edit_tagline", listing.get("promotional_tagline") or "")
            cur_desc = st.session_state.get("edit_description", listing.get("description", ""))
            cur_features = listing.get("features", [])
            cur_keywords = listing.get("keywords", [])
            cur_specifics = listing.get("item_specifics", {})
            cur_missing = listing.get("missing_info", [])

            # ----------------------------------------------------
            # TAB 1: BUYER-FACING MARKETPLACE PREVIEW
            # ----------------------------------------------------
            with tab_preview:
                st.markdown('<div class="ip-marketplace-card">', unsafe_allow_html=True)

                # Title & Subtitle Display
                st.markdown(f'<div class="ip-preview-title">{cur_title}</div>', unsafe_allow_html=True)
                if cur_tagline:
                    st.markdown(f'<div class="ip-preview-tagline">{cur_tagline}</div>', unsafe_allow_html=True)

                # Thumbnail + Quick Specifics Card
                prev_col1, prev_col2 = st.columns([1, 2])
                with prev_col1:
                    if st.session_state.image_bytes:
                        st.image(st.session_state.image_bytes, caption="Listing Photo", use_container_width=True)
                with prev_col2:
                    st.markdown("**Product Specifics:**")
                    for k, v in cur_specifics.items():
                        if v and str(v).strip() and str(v).strip().lower() != "null":
                            st.markdown(f"• **{k.capitalize()}:** {v}")

                # Key Highlights & Benefits
                if cur_features:
                    st.markdown('<div class="ip-section-title">Key Highlights & Benefits</div>', unsafe_allow_html=True)
                    for f in cur_features:
                        st.markdown(f"• {f}")

                # Detailed Item Description
                st.markdown('<div class="ip-section-title">Product Description</div>', unsafe_allow_html=True)
                for p in cur_desc.split("\n\n"):
                    if p.strip():
                        st.write(p.strip())

                st.markdown("</div>", unsafe_allow_html=True)

                # SELLER-ONLY CHECKLIST (Strictly separated from buyer preview)
                if cur_missing:
                    st.markdown(
                        """
                        <div style="background-color: #FFFBEB; border: 1px solid #FDE68A; border-radius: 6px; padding: 0.9rem; margin-top: 1rem;">
                            <div style="font-weight: 700; color: #92400E; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem;">
                                Pre-Listing Verification Checklist (Seller-Only)
                            </div>
                            <div style="font-size: 0.78rem; color: #78350F; margin-bottom: 0.5rem;">
                                These items were flagged by the AI for your confirmation and are <strong>not</strong> published to buyers:
                            </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    for idx, item in enumerate(cur_missing, 1):
                        st.markdown(f"**{idx}.** {item}")
                    st.markdown("</div>", unsafe_allow_html=True)

            # ----------------------------------------------------
            # TAB 2: EDITABLE FIELDS
            # ----------------------------------------------------
            with tab_edit:
                st.markdown("##### Listing Title")
                title_val = st.text_input(
                    "Listing Title",
                    value=cur_title,
                    key="edit_title",
                    label_visibility="collapsed",
                    help="eBay limits listing titles to 80 characters. Maximize relevant search keywords.",
                )

                # Live character count indicator
                t_len = len(title_val)
                chars_remaining = MAX_TITLE_LENGTH - t_len
                if t_len <= MAX_TITLE_LENGTH:
                    st.markdown(
                        f'<div class="ip-char-counter"><span class="ip-char-ok">{t_len} / {MAX_TITLE_LENGTH} characters</span><span>{chars_remaining} remaining</span></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="ip-char-counter"><span class="ip-char-warn">⚠️ {t_len} / {MAX_TITLE_LENGTH} characters</span><span class="ip-char-warn">Exceeds limit by {abs(chars_remaining)} characters!</span></div>',
                        unsafe_allow_html=True,
                    )

                st.markdown("##### Promotional Subtitle (Optional)")
                tagline_val = st.text_input(
                    "Promotional Subtitle",
                    value=cur_tagline,
                    key="edit_tagline",
                    label_visibility="collapsed",
                    placeholder="Optional promotional highlight or subtitle (eBay allows up to 55 characters)",
                    help="Optional marketing subtitle for your eBay listing."
                )
                sub_len = len(tagline_val)
                if sub_len > 0:
                    if sub_len <= 55:
                        st.caption(f"{sub_len} / 55 characters used")
                    else:
                        st.caption(f"⚠️ {sub_len} / 55 characters (exceeds standard 55-char eBay subtitle)")

                st.markdown("##### Item Specifics")
                spec_cols = st.columns(2)
                updated_specifics = {}
                keys = list(cur_specifics.keys())
                for i, k in enumerate(keys):
                    curr_val = cur_specifics[k] or ""
                    target_col = spec_cols[i % 2]
                    with target_col:
                        label = k.replace("_", " ").capitalize()
                        new_val = st.text_input(label, value=curr_val, key=f"spec_{k}")
                        updated_specifics[k] = new_val.strip() if new_val.strip() else None

                st.markdown("##### Key Features (Bullets)")
                features_raw = "\n".join(cur_features)
                updated_features_text = st.text_area(
                    "Key Features",
                    value=features_raw,
                    height=120,
                    key="edit_features",
                    label_visibility="collapsed",
                    help="One feature bullet point per line."
                )
                updated_features = [line.strip("- •* ") for line in updated_features_text.split("\n") if line.strip()]

                st.markdown("##### Search Keywords & Tags")
                keywords_raw = ", ".join(cur_keywords)
                updated_keywords_text = st.text_input(
                    "Keywords",
                    value=keywords_raw,
                    key="edit_keywords",
                    label_visibility="collapsed",
                    help="Comma-separated keywords buyers use when searching on eBay."
                )
                updated_keywords = [k.strip() for k in updated_keywords_text.split(",") if k.strip()]

                st.markdown("##### Item Description")
                updated_desc = st.text_area(
                    "Full eBay Item Description",
                    value=cur_desc,
                    height=200,
                    key="edit_description",
                    label_visibility="collapsed",
                    help="Comprehensive item description formatted for clarity and buyer confidence."
                )

            # ----------------------------------------------------
            # TAB 3: EXPORT & ONE-CLICK COPY
            # ----------------------------------------------------
            with tab_export:
                # Use current values from edit tab if touched, otherwise from listing
                active_title = st.session_state.get("edit_title", cur_title)
                active_tagline = st.session_state.get("edit_tagline", cur_tagline)
                active_desc = st.session_state.get("edit_description", cur_desc)
                active_features = [line.strip("- •* ") for line in st.session_state.get("edit_features", "\n".join(cur_features)).split("\n") if line.strip()]
                active_keywords = [k.strip() for k in st.session_state.get("edit_keywords", ", ".join(cur_keywords)).split(",") if k.strip()]
                active_specifics = {k: st.session_state.get(f"spec_{k}", cur_specifics.get(k)) for k in cur_specifics.keys()}

                st.markdown("##### Quick Copy Snippets")
                st.caption("Click the copy icon on any code snippet to copy individual sections directly:")

                st.caption("Title:")
                st.code(active_title, language=None)

                if active_tagline:
                    st.caption("Subtitle / Tagline:")
                    st.code(active_tagline, language=None)

                st.caption("Description (Plain Text):")
                st.code(active_desc, language=None)

                st.caption("Key Features & Benefits:")
                st.code("\n".join(f"• {f}" for f in active_features), language=None)

                st.caption("Search Keywords:")
                st.code(", ".join(active_keywords), language=None)

                st.divider()

                st.markdown("##### Download Files")
                st.caption("Export your listing for eBay's description editor or inventory management:")

                # Generate clean HTML and TXT payloads
                final_html_payload = build_export_html(
                    title=active_title,
                    description=active_desc,
                    features=active_features,
                    specifics=active_specifics,
                    tagline=active_tagline or None,
                )

                final_txt_payload = build_export_txt(
                    title=active_title,
                    description=active_desc,
                    features=active_features,
                    keywords=active_keywords,
                    specifics=active_specifics,
                    missing_info=cur_missing,
                    tagline=active_tagline or None,
                )

                final_json_payload = {
                    "title": active_title,
                    "promotional_tagline": active_tagline or None,
                    "description": active_desc,
                    "features": active_features,
                    "keywords": active_keywords,
                    "item_specifics": active_specifics,
                    "missing_info": cur_missing,
                }

                d_col1, d_col2, d_col3 = st.columns([1, 1, 1])
                with d_col1:
                    st.download_button(
                        label="Download Clean HTML",
                        data=final_html_payload,
                        file_name="ebay_description.html",
                        mime="text/html",
                        use_container_width=True,
                        help="Clean, mobile-responsive HTML ready to paste into eBay's description HTML tab."
                    )
                with d_col2:
                    st.download_button(
                        label="Download Full TXT",
                        data=final_txt_payload,
                        file_name="ebay_listing.txt",
                        mime="text/plain",
                        use_container_width=True,
                        help="Plain text file containing title, specifics, bullet points, and description."
                    )
                with d_col3:
                    st.download_button(
                        label="Download JSON Data",
                        data=json.dumps(final_json_payload, indent=2),
                        file_name="ebay_listing.json",
                        mime="application/json",
                        use_container_width=True,
                        help="Structured JSON format for programmatic use or inventory management."
                    )


if __name__ == "__main__":
    main()
