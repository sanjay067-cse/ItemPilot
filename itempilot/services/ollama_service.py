"""Ollama API integration service for local inference with Gemma 3."""

import json
from typing import Any, Dict, List, Optional, Tuple
import requests

from itempilot.config import DEFAULT_MODEL, OLLAMA_BASE_URL, REQUEST_TIMEOUT


class OllamaServiceError(Exception):
    """Base exception for Ollama communication errors."""
    pass


class OllamaConnectionError(OllamaServiceError):
    """Raised when Ollama server cannot be reached."""
    pass


class OllamaModelNotFoundError(OllamaServiceError):
    """Raised when requested model is not pulled in Ollama."""
    pass


class OllamaService:
    """Service to communicate with local Ollama server."""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: int = REQUEST_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def check_connection(self) -> Tuple[bool, str]:
        """Check if local Ollama daemon is active and responding."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                return True, "Ollama is running."
            return False, f"Ollama returned HTTP status {resp.status_code}."
        except requests.exceptions.ConnectionError:
            return False, f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?"
        except requests.exceptions.Timeout:
            return False, f"Connection to Ollama at {self.base_url} timed out."
        except Exception as e:
            return False, f"Ollama connection check failed: {str(e)}"

    def list_installed_models(self) -> List[str]:
        """Get list of model names currently installed in local Ollama."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return [m for m in models if m]
            return []
        except Exception:
            return []

    def is_model_available(self, model_name: Optional[str] = None) -> bool:
        """Check if the specified model is present locally."""
        target = (model_name or self.model).lower()
        target_base = target.split(":")[0]
        installed = self.list_installed_models()
        for m in installed:
            m_lower = m.lower()
            if m_lower == target or m_lower.startswith(f"{target}:") or m_lower.split(":")[0] == target_base:
                return True
        return False

    def get_service_status(self) -> Dict[str, Any]:
        """Comprehensive status report of Ollama and model availability in a single request."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if resp.status_code != 200:
                return {
                    "reachable": False,
                    "model_available": False,
                    "installed_models": [],
                    "target_model": self.model,
                    "message": f"Ollama returned HTTP status {resp.status_code}.",
                }

            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            target = self.model.lower()
            target_base = target.split(":")[0]
            model_ok = any(
                m.lower() == target or m.lower().startswith(f"{target}:") or m.lower().split(":")[0] == target_base
                for m in models
            )

            if model_ok:
                msg = f"Ollama online. Model '{self.model}' is available."
            else:
                msg = f"Ollama online, but '{self.model}' is not pulled. Run: `ollama run {self.model}`"

            return {
                "reachable": True,
                "model_available": model_ok,
                "installed_models": models,
                "target_model": self.model,
                "message": msg,
            }
        except requests.exceptions.ConnectionError:
            return {
                "reachable": False,
                "model_available": False,
                "installed_models": [],
                "target_model": self.model,
                "message": f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?",
            }
        except requests.exceptions.Timeout:
            return {
                "reachable": False,
                "model_available": False,
                "installed_models": [],
                "target_model": self.model,
                "message": f"Connection to Ollama at {self.base_url} timed out.",
            }
        except Exception as e:
            return {
                "reachable": False,
                "model_available": False,
                "installed_models": [],
                "target_model": self.model,
                "message": f"Ollama connection check failed: {str(e)}",
            }

    def generate(
        self,
        prompt: str,
        image_base64: Optional[str] = None,
        system_prompt: Optional[str] = None,
        format_json: bool = True,
    ) -> str:
        """Send prompt and optional image to Ollama for local generation."""
        endpoint = f"{self.base_url}/api/generate"

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        if system_prompt:
            payload["system"] = system_prompt

        if image_base64:
            payload["images"] = [image_base64]

        if format_json:
            payload["format"] = "json"

        try:
            resp = requests.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )
        except requests.exceptions.ConnectionError as e:
            raise OllamaConnectionError(
                f"Failed to connect to Ollama at {self.base_url}. Ensure the Ollama service is running."
            ) from e
        except requests.exceptions.Timeout as e:
            raise OllamaServiceError(
                f"Ollama request timed out after {self.timeout} seconds. The model may still be loading."
            ) from e
        except Exception as e:
            raise OllamaServiceError(f"Unexpected error communicating with Ollama: {str(e)}") from e

        if resp.status_code == 404:
            raise OllamaModelNotFoundError(
                f"Model '{self.model}' not found in Ollama. Run: `ollama run {self.model}`"
            )

        if resp.status_code != 200:
            raise OllamaServiceError(
                f"Ollama API returned HTTP {resp.status_code}: {resp.text}"
            )

        data = resp.json()
        response_text = data.get("response", "")
        if not response_text:
            raise OllamaServiceError("Ollama returned an empty response.")

        return response_text
