# ItemPilot 🚀

### Turn product photos into buyer-focused eBay listings with local AI.

ItemPilot is a local-first AI application that helps online sellers turn product photos and product details into compelling, editable eBay listing drafts using **Gemma 3 4B and Ollama**.

Instead of starting from a blank page, sellers can upload a product photo, provide the details they know, and generate a polished listing they can review and refine before publishing.

## ✨ Features

- **📸 Image-based listing generation** — Analyze an uploaded product photo using Gemma 3 4B's vision capabilities.
- **✍️ Buyer-focused copywriting** — Generate engaging, natural product descriptions that highlight the benefits of confirmed features.
- **🔎 Search-friendly titles** — Create relevant eBay listing titles with an 80-character limit.
- **📋 Structured listing details** — Generate product descriptions, key features, item specifics, and relevant search keywords.
- **🛡️ Accuracy safeguards** — Identify missing information and prompt sellers to confirm important details rather than blindly trusting AI-generated claims.
- **✏️ Editable results** — Review and refine listing content before using it.
- **📥 Export options** — Copy generated content and download listing descriptions in supported formats.
- **🏠 Local AI inference** — Run the model through Ollama on your own computer without relying on a hosted AI API for generation.

## 🧠 How It Works

1. **Upload:** Add a photo of the product you want to list.
2. **Describe:** Enter any known details, such as brand, model, condition, colour, dimensions, and features.
3. **Generate:** ItemPilot sends the image and supplied details to your local Gemma 3 4B model through Ollama.
4. **Review:** Inspect and edit the generated title, description, features, and other listing details.
5. **Export:** Copy or download the listing for further editing and use on eBay.

ItemPilot generates listing drafts. It does not automatically publish products to eBay.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application logic and AI integration |
| Streamlit | Interactive user interface |
| Gemma 3 4B | Local image understanding and text generation |
| Ollama | Local model runtime |
| Pydantic | Structured output validation |
| Pillow | Image processing and validation |
| Requests | HTTP communication |
| Pytest | Automated testing |

## 🔐 Why Local AI?

Product photos, supplier information, and seller notes can contain information that users may prefer to keep on their own devices.

ItemPilot uses Gemma 3 4B through a local Ollama instance rather than sending generation requests to a hosted AI API.

This approach offers:

- **Greater control over data:** Images and prompts are processed through the local model endpoint.
- **Offline inference:** Once the application dependencies and model are installed, generation can work without an internet connection, provided the local services are available.
- **Reduced reliance on cloud APIs:** The core AI workflow does not require a paid hosted inference API.
- **Flexibility:** The project can be extended to support additional compatible local models.

Local inference does not by itself guarantee that all system logs, temporary files, or other local data are automatically deleted. Review the application's data-handling behaviour before using sensitive information.

## 🚀 Getting Started

### Prerequisites

- Windows, macOS, or Linux
- Python
- [Ollama](https://ollama.com/download)
- The `gemma3:4b` model downloaded through Ollama

The commands below use Windows PowerShell.

### 1. Clone the repository

```powershell
git clone https://github.com/sanjay067-cse/ItemPilot.git
cd ItemPilot
```

### 2. Create a virtual environment

```powershell
py -m venv .venv
```

### 3. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Install the Gemma model

Install Ollama first, then run:

```powershell
ollama pull gemma3:4b
```

This model download is normally a one-time setup step. You do not need to download it again each time you start ItemPilot.

### 5. Launch ItemPilot

Ensure Ollama is running, then execute:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL displayed in the terminal, usually:

`http://localhost:8501`

### Run the Tests

To run the automated test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

The test suite covers configuration, image validation, structured listing data, listing-service behaviour, title validation, and export functionality.

## 📁 Project Structure

```text
ItemPilot/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── .streamlit/
│   └── config.toml
├── itempilot/
│   ├── config.py
│   ├── schemas.py
│   ├── prompts/
│   │   └── listing_prompt.txt
│   ├── services/
│   │   ├── image_service.py
│   │   ├── listing_service.py
│   │   └── ollama_service.py
│   └── utils/
│       ├── export.py
│       └── validation.py
└── tests/
    ├── test_config.py
    ├── test_export.py
    ├── test_schemas.py
    ├── test_services.py
    └── test_validation.py
```

## ⚠️ Important Limitations

- AI-generated listings can contain mistakes. Always review them before publishing.
- A product image cannot reliably establish every specification, model number, material, or operational condition.
- Sellers should verify important details and disclose known defects.
- ItemPilot does not determine competitive prices, guarantee sales, or automatically publish listings to eBay.
- Performance depends on the local computer's available memory and processing resources.

## 🗺️ Possible Future Improvements

- Support for more product categories and specialised listing templates.
- Additional local vision-language models.
- Improved preview and editing workflows.
- Feedback from real online sellers to improve listing quality.
- Optional integrations with marketplace APIs.

## 🤝 Contributing

Suggestions, bug reports, and contributions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Make your changes and add tests where appropriate.
4. Run the test suite.
5. Open a pull request describing your changes.

## 📄 License

This project is distributed under the MIT License. See [LICENSE](LICENSE).

Review the applicable Gemma terms for model-specific usage and redistribution requirements.

## 👨‍💻 Author

**Sanjay Kumar Mahto**

GitHub: [@sanjay067-cse](https://github.com/sanjay067-cse)

Project: [ItemPilot](https://github.com/sanjay067-cse/ItemPilot)

---

*Built with Python, Streamlit, Gemma 3 4B, and Ollama.*