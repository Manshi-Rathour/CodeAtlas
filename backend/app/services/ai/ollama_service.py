import httpx

from app.core.config import settings


# Keep local inference requests bounded without blocking the app forever.
REQUEST_TIMEOUT_SECONDS = 600.0

# Maximum error text included in API responses.
MAX_ERROR_DETAIL_CHARS = 300


def _shorten_error(text: str) -> str:
    """Keep Ollama error details short and free of huge payloads."""

    cleaned = " ".join((text or "").split())

    return cleaned[:MAX_ERROR_DETAIL_CHARS]


class OllamaService:
    """
    Handles communication with the local Ollama LLM server.

    The service never exposes credentials or prompt contents in errors.
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str | None = None
    ) -> str:
        """
        Generate a response using the configured Ollama model.

        Raises RuntimeError with a user-safe message when Ollama is
        unavailable, times out, returns an HTTP error, or returns
        an empty response.
        """

        if not prompt or not prompt.strip():
            raise RuntimeError("The AI prompt cannot be empty.")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT_SECONDS
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )

                response.raise_for_status()

                result = response.json()

                answer = (result.get("response") or "").strip()

                if not answer:
                    raise RuntimeError(
                        "Ollama returned an empty response. "
                        "Try a shorter question or check the model."
                    )

                return answer

        except httpx.TimeoutException:
            raise RuntimeError(
                "Ollama request timed out. Please try again."
            )

        except httpx.ConnectError:
            raise RuntimeError(
                "Could not connect to Ollama. Make sure Ollama is running."
            )

        except httpx.HTTPStatusError as error:
            detail = _shorten_error(error.response.text)

            raise RuntimeError(
                "Ollama returned an error"
                + (f": {detail}" if detail else ".")
            )

        except httpx.HTTPError:
            raise RuntimeError(
                "Could not communicate with Ollama. "
                "Please check the local AI server."
            )

        except ValueError:
            raise RuntimeError(
                "Ollama returned an invalid response."
            )

    async def check_status(self) -> dict:
        """
        Check whether Ollama is reachable and the configured model exists.

        Used for integration verification and diagnostics.
        """

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/tags"
                )

                response.raise_for_status()

                data = response.json()

        except httpx.TimeoutException:
            raise RuntimeError("Ollama status check timed out.")

        except httpx.ConnectError:
            raise RuntimeError(
                "Could not connect to Ollama. Make sure Ollama is running."
            )

        except httpx.HTTPError as error:
            detail = _shorten_error(str(error))

            raise RuntimeError(
                "Could not read Ollama status"
                + (f": {detail}" if detail else ".")
            )

        except ValueError:
            raise RuntimeError("Ollama returned an invalid status response.")

        models = [
            model.get("name", "")
            for model in data.get("models", [])
            if isinstance(model, dict)
        ]

        return {
            "available": True,
            "model": self.model,
            "model_available": self.model in models,
            "models": models,
        }


ollama_service = OllamaService()
