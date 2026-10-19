"""Service orchestrating prompt assembly, AI inference, and listing validation."""

from pathlib import Path
from typing import Optional

from itempilot.config import LISTING_PROMPT_PATH
from itempilot.schemas import ListingOutput, SellerInput
from itempilot.services.image_service import ImageService, ImageValidationError
from itempilot.services.ollama_service import OllamaService
from itempilot.utils.validation import (
    detect_missing_fields,
    enforce_title_length,
    parse_and_clean_json,
)


class ListingServiceError(Exception):
    """Raised when listing generation or parsing fails."""
    pass


class ListingService:
    """Orchestrates image validation, prompt construction, Ollama generation, and parsing."""

    def __init__(
        self,
        ollama_service: Optional[OllamaService] = None,
        prompt_path: Path = LISTING_PROMPT_PATH,
    ):
        self.ollama = ollama_service or OllamaService()
        self.prompt_path = prompt_path

    def load_system_prompt(self) -> str:
        """Load system prompt from template file."""
        if not self.prompt_path.exists():
            raise FileNotFoundError(f"Listing prompt file not found at {self.prompt_path}")
        return self.prompt_path.read_text(encoding="utf-8").strip()

    def build_user_prompt(self, seller_input: Optional[SellerInput] = None) -> str:
        """Construct user message combining seller details and instruction."""
        details = seller_input or SellerInput()
        lines = [
            "Analyze the attached product image and generate a structured eBay listing.",
            "",
            "SELLER-PROVIDED DETAILS (prioritize these if accurate):",
            f"- Category / Product Name: {details.category or 'Not specified'}",
            f"- Brand: {details.brand or 'Not specified (verify visually or set null)'}",
            f"- Model / SKU: {details.model_sku or 'Not specified'}",
            f"- Item Condition: {details.condition or 'Not specified by seller (assess visually if evident, otherwise flag in missing_info)'}",
            f"- Color: {details.color or 'Determine from photo'}",
            f"- Material: {details.material or 'Determine from photo if obvious, else null'}",
            f"- Size / Dimensions: {details.size_dimensions or 'Not specified'}",
            f"- Notable Features / Inclusions: {details.features or 'None specified'}",
            f"- Desired Writing Style: {details.writing_style or 'Clear and informative'}",
            "",
            "COPYWRITING & INTEGRITY INSTRUCTIONS:",
            "1. Output ONLY a valid JSON object matching the requested schema.",
            "2. 'title' MUST be 80 characters or fewer. Brand and primary keywords first. Natural phrasing, no keyword stuffing.",
            "3. Answer the buyer's 3 key questions: What is this product? Why is it useful or appealing? What do I need to know before buying?",
            "4. Turn confirmed features into practical buyer benefits (e.g., folding hinge -> easy commute storage). Never invent unconfirmed specs or benefits.",
            "5. Publishable buyer text ('description', 'features', 'title') must remain clean and professional. NEVER put internal AI warnings or verification questions in the description; place them ONLY in 'missing_info'.",
            "6. Never claim the item is tested or working unless explicitly stated in seller details.",
            "7. Do NOT guess invisible specs (battery runtime, internal chips, authenticity). Flag unknown points in 'missing_info'.",
        ]
        return "\n".join(lines)

    def generate_listing(
        self,
        image_bytes: bytes,
        filename: Optional[str] = None,
        seller_input: Optional[SellerInput] = None,
        allow_retry: bool = True,
    ) -> ListingOutput:
        """Generate a validated ListingOutput from image bytes and seller input."""
        # 1. Validate image
        is_valid, err = ImageService.validate_image_file(image_bytes, filename=filename)
        if not is_valid:
            raise ImageValidationError(err or "Uploaded image is invalid.")

        image_b64 = ImageService.encode_to_base64(image_bytes)
        system_prompt = self.load_system_prompt()
        user_prompt = self.build_user_prompt(seller_input)

        # 2. Call Ollama
        raw_response = self.ollama.generate(
            prompt=user_prompt,
            image_base64=image_b64,
            system_prompt=system_prompt,
            format_json=True,
        )

        # 3. Parse & validate
        try:
            return self._parse_and_validate(raw_response)
        except Exception as first_err:
            if not allow_retry:
                raise ListingServiceError(
                    f"Failed to generate valid listing schema: {str(first_err)}"
                ) from first_err

            # Single retry with explicit correction prompt
            retry_prompt = (
                f"{user_prompt}\n\n"
                f"ATTENTION: Your previous response was invalid with error: '{str(first_err)}'.\n"
                "Return ONLY a clean JSON object matching the schema. "
                "Ensure 'title' is strictly under 80 characters and all required fields exist."
            )

            try:
                retry_response = self.ollama.generate(
                    prompt=retry_prompt,
                    image_base64=image_b64,
                    system_prompt=system_prompt,
                    format_json=True,
                )
                return self._parse_and_validate(retry_response)
            except Exception as second_err:
                raise ListingServiceError(
                    f"Model output validation failed after retry: {str(second_err)}"
                ) from second_err

    def _parse_and_validate(self, raw_text: str) -> ListingOutput:
        """Parse raw response text, clean fields, and construct ListingOutput."""
        data = parse_and_clean_json(raw_text)
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object, got {type(data).__name__}")

        # Ensure title does not exceed 80 characters
        title = data.get("title")
        if not title:
            raise ValueError("Model response missing required 'title' field.")
        data["title"] = enforce_title_length(str(title), max_chars=80)

        # Ensure description is present
        desc = data.get("description")
        if not desc:
            raise ValueError("Model response missing required 'description' field.")
        data["description"] = str(desc).strip()

        # Handle optional promotional tagline
        tagline = data.get("promotional_tagline")
        if tagline and str(tagline).strip() and str(tagline).strip().lower() != "null":
            data["promotional_tagline"] = str(tagline).strip()
        else:
            data["promotional_tagline"] = None

        # Ensure features, keywords, missing_info are lists of strings
        for list_key in ("features", "keywords", "missing_info"):
            val = data.get(list_key)
            if isinstance(val, list):
                data[list_key] = [str(item).strip() for item in val if str(item).strip()]
            elif isinstance(val, str) and val.strip():
                data[list_key] = [line.strip("- •* ") for line in val.split("\n") if line.strip()]
            else:
                data[list_key] = []

        # Ensure item_specifics is dict
        specifics = data.get("item_specifics")
        if not isinstance(specifics, dict):
            data["item_specifics"] = {}
        else:
            data["item_specifics"] = {
                str(k): (str(v).strip() if v is not None else None)
                for k, v in specifics.items()
            }

        # Supplement missing info with detected empty fields if not already mentioned
        missing_keys = detect_missing_fields(data["item_specifics"])
        for k in missing_keys:
            note = f"Specific '{k}' is unconfirmed. Verify or add value if known."
            if not any(k.lower() in m.lower() for m in data["missing_info"]):
                data["missing_info"].append(note)

        # Final Pydantic validation
        return ListingOutput(**data)
