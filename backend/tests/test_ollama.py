import asyncio

import httpx
import pytest

from app.services.ai import ollama_service as ollama_module
from app.services.ai.ollama_service import OllamaService


class FakeResponse:
    def __init__(self, payload=None, status_code=200, text="", invalid_json=False):
        self._payload = payload
        self.status_code = status_code
        self.text = text
        self._invalid_json = invalid_json
        self.request = httpx.Request("POST", "http://localhost:11434/api/generate")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=self.request,
                response=httpx.Response(
                    self.status_code,
                    request=self.request,
                    text=self.text,
                ),
            )

    def json(self):
        if self._invalid_json:
            raise ValueError("Invalid JSON")

        return self._payload


def install_fake_client(monkeypatch, response=None, error=None):
    """
    Replace only httpx.AsyncClient so the service still catches
    the real httpx exception classes.
    """

    captured = {}

    class FakeAsyncClient:
        def __init__(self, timeout=None, **kwargs):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, url, json=None):
            captured["url"] = url
            captured["payload"] = json

            if error is not None:
                raise error

            return response

        async def get(self, url):
            captured["url"] = url

            if error is not None:
                raise error

            return response

    monkeypatch.setattr(
        ollama_module.httpx,
        "AsyncClient",
        FakeAsyncClient,
    )

    return captured


def test_generate_response_success(monkeypatch):
    captured = install_fake_client(
        monkeypatch,
        response=FakeResponse({"response": "  Hello developer.  "}),
    )

    service = OllamaService()

    answer = asyncio.run(service.generate_response(
        prompt="Explain main.",
        system_prompt="You are a code assistant.",
    ))

    assert answer == "Hello developer."
    assert captured["payload"]["model"] == service.model
    assert captured["payload"]["system"] == "You are a code assistant."
    assert captured["payload"]["stream"] is False
    assert captured["url"].endswith("/api/generate")


def test_generate_response_omits_missing_system_prompt(monkeypatch):
    captured = install_fake_client(
        monkeypatch,
        response=FakeResponse({"response": "Answer"}),
    )

    service = OllamaService()

    asyncio.run(service.generate_response(prompt="Explain main."))

    assert "system" not in captured["payload"]


def test_generate_response_rejects_empty_prompt(monkeypatch):
    captured = install_fake_client(
        monkeypatch,
        response=FakeResponse({"response": "unused"}),
    )

    service = OllamaService()

    with pytest.raises(RuntimeError, match="prompt cannot be empty"):
        asyncio.run(service.generate_response(prompt="   "))

    assert "payload" not in captured


def test_generate_response_handles_empty_answer(monkeypatch):
    install_fake_client(
        monkeypatch,
        response=FakeResponse({"response": "   "}),
    )

    service = OllamaService()

    with pytest.raises(RuntimeError, match="empty response"):
        asyncio.run(service.generate_response(prompt="Explain main."))


def test_generate_response_handles_connection_error(monkeypatch):
    install_fake_client(
        monkeypatch,
        error=httpx.ConnectError("connection refused"),
    )

    service = OllamaService()

    with pytest.raises(RuntimeError, match="Could not connect to Ollama"):
        asyncio.run(service.generate_response(prompt="Explain main."))


def test_generate_response_handles_timeout(monkeypatch):
    install_fake_client(
        monkeypatch,
        error=httpx.TimeoutException("timed out"),
    )

    service = OllamaService()

    with pytest.raises(RuntimeError, match="timed out"):
        asyncio.run(service.generate_response(prompt="Explain main."))


def test_generate_response_handles_http_error(monkeypatch):
    install_fake_client(
        monkeypatch,
        response=FakeResponse(
            status_code=500,
            text="model not found",
        ),
    )

    service = OllamaService()

    with pytest.raises(RuntimeError) as error:
        asyncio.run(service.generate_response(prompt="Explain main."))

    assert "Ollama returned an error" in str(error.value)
    assert "model not found" in str(error.value)


def test_generate_response_handles_invalid_json(monkeypatch):
    install_fake_client(
        monkeypatch,
        response=FakeResponse(invalid_json=True),
    )

    service = OllamaService()

    with pytest.raises(RuntimeError, match="invalid response"):
        asyncio.run(service.generate_response(prompt="Explain main."))


def test_check_status_reports_configured_model(monkeypatch):
    install_fake_client(
        monkeypatch,
        response=FakeResponse({
            "models": [
                {"name": "qwen2.5-coder:7b"},
                {"name": "llama3:8b"},
            ]
        }),
    )

    service = OllamaService()
    service.model = "qwen2.5-coder:7b"

    status = asyncio.run(service.check_status())

    assert status["available"] is True
    assert status["model_available"] is True
    assert status["model"] == "qwen2.5-coder:7b"
    assert "llama3:8b" in status["models"]


def test_check_status_reports_missing_model(monkeypatch):
    install_fake_client(
        monkeypatch,
        response=FakeResponse({"models": [{"name": "llama3:8b"}]}),
    )

    service = OllamaService()
    service.model = "qwen2.5-coder:7b"

    status = asyncio.run(service.check_status())

    assert status["available"] is True
    assert status["model_available"] is False


def test_check_status_handles_connection_error(monkeypatch):
    install_fake_client(
        monkeypatch,
        error=httpx.ConnectError("connection refused"),
    )

    service = OllamaService()

    with pytest.raises(RuntimeError, match="Could not connect to Ollama"):
        asyncio.run(service.check_status())
