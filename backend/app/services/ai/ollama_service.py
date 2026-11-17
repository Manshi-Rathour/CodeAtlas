import httpx

from app.core.config import settings


class OllamaService:
    """
    Handles communication with the local Ollama LLM server.
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
        """

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )

                response.raise_for_status()

                result = response.json()

                return result.get("response", "").strip()

        except httpx.TimeoutException:
            raise RuntimeError(
                "Ollama request timed out. Please try again."
            )

        except httpx.ConnectError:
            raise RuntimeError(
                "Could not connect to Ollama. Make sure Ollama is running."
            )

        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                f"Ollama returned an error: {error.response.text}"
            )


ollama_service = OllamaService()
