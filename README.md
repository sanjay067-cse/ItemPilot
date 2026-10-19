# ItemPilot — Local AI eBay Listing Assistant

**ItemPilot** is a local-first eBay listing assistant designed to generate compelling, buyer-oriented, and search-optimized eBay listings directly from product photos and optional seller notes. Powered by **Gemma 3 (4B)** via **Ollama**, ItemPilot executes inference locally on your machine without transmitting product images or listing data to third-party cloud AI APIs.

---

## Features

- **E-Commerce Copywriter Intelligence**: Answers the 3 essential questions for prospective buyers: *What is this product? Why is it useful or appealing? What do I need to know before buying?* Translates confirmed features into practical, everyday buyer benefits without inventing claims.
- **Category-Aware Prompting**: Automatically adapts tone, vocabulary, and organization depending on whether the product is consumer electronics, home/kitchen goods, apparel/footwear, or vintage collectibles.
- **Copywriting Style Selector**: Allows sellers to tailor listing tone between **Clear and informative**, **Benefit-focused**, and **Concise**.
- **Strict Hallucination Guard**: Prompt-engineered and schema-validated to describe only visible details and seller-provided facts. Unknown attributes are explicitly returned as `null` and flagged in a separate seller-only checklist rather than fabricated into buyer-facing copy.
- **eBay Title & Subtitle Optimization**: Produces search-optimized eBay titles strictly constrained to **≤ 80 characters** and optional promotional subtitles (≤ 55 chars) with real-time character counters.
- **Realistic Marketplace Preview**: Dedicated preview tab displays an authentic e-commerce card with photo thumbnail, title, specifics, bullet highlights, and description, clearly distinguishing buyer-facing copy from the seller's internal verification checklist.
- **Multi-Format Export & One-Click Copy**: Download listings as mobile-responsive, cleanly formatted, and safely escaped HTML (`.html`), formatted plain text (`.txt`), or structured JSON (`.json`), plus instant section-by-section clipboard copying.
- **Comprehensive Offline Tests**: Tested with `pytest` using mocked endpoints—no active GPU or network connection required for CI/CD.

---

## Project Architecture

```
itempilot/
├── .streamlit/
│   └── config.toml                  # Streamlit clean UI theme configuration
├── itempilot/
│   ├── __init__.py                  # Package init
│   ├── config.py                    # Environment variables and defaults
│   ├── schemas.py                   # Pydantic models for inputs and listing JSON
│   ├── prompts/
│   │   └── listing_prompt.txt       # E-commerce copywriter prompt with hallucination guard
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_service.py         # Image validation (size, type, PIL check) & Base64
│   │   ├── listing_service.py       # Orchestration, retry loop, and JSON parsing
│   │   └── ollama_service.py        # Local Ollama REST client & status monitoring
│   └── utils/
│       ├── __init__.py
│       ├── export.py                # Safe HTML and TXT export generator (XSS protected)
│       └── validation.py            # Title truncating, missing field detector, JSON parser
├── tests/
│   ├── __init__.py
│   ├── test_export.py               # Safe HTML escaping and text export tests
│   ├── test_schemas.py              # Pydantic schema validation tests
│   ├── test_services.py             # Service logic, retries, and mocked Ollama tests
│   └── test_validation.py           # Title length, missing info, and JSON extractor tests
├── app.py                           # Streamlit dual-panel web application
├── requirements.txt                 # Dependencies
├── LICENSE                          # MIT License
└── README.md                        # Documentation
```

---

## Quick Start

### 1. Prerequisites & Ollama Setup

Install [Ollama](https://ollama.ai) and pull the multimodal `gemma3:4b` model:

```bash
# Pull the Gemma 3 4B vision model
ollama pull gemma3:4b

# Ensure Ollama server is running (default: http://localhost:11434)
ollama serve
```

### 2. Install ItemPilot Dependencies

In your project directory:

```bash
pip install -r requirements.txt
```

### 3. Launch the Application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## Running Tests

ItemPilot includes an offline test suite mocking all external calls:

```bash
pytest -v
```

---

## Configuration

ItemPilot can be customized using environment variables:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama service endpoint |
| `ITEMPILOT_MODEL` | `gemma3:4b` | Default vision model |
| `ITEMPILOT_TIMEOUT` | `120` | Inference request timeout (seconds) |

---

## License

Distributed under the [MIT License](LICENSE).
