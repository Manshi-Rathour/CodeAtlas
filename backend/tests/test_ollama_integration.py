import asyncio
import os

import pytest

from app.services.ai.ollama_service import ollama_service


pytestmark = pytest.mark.skipif(
    os.getenv("CODEATLAS_RUN_OLLAMA_TESTS") != "1",
    reason=(
        "Set CODEATLAS_RUN_OLLAMA_TESTS=1 to run the real local "
        "Ollama integration test."
    ),
)


def test_real_ollama_connection_model_and_generation():
    """
    Real integration test against the local Ollama server.

    It is skipped by default so the normal test suite never
    requires a running LLM.
    """

    status = asyncio.run(ollama_service.check_status())

    assert status["available"] is True
    assert status["models"], "Ollama reported no installed models."
    assert status["model_available"] is True

    answer = asyncio.run(ollama_service.generate_response(
        prompt="Reply with exactly the single word: ready",
        system_prompt=(
            "You are a connectivity test. Reply with one word only."
        ),
    ))

    assert answer.strip()
