from collections.abc import Generator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app, get_openai_client


client = TestClient(app)


class FakeResponses:
    def __init__(self, output_text: str = "안녕하세요! 무엇을 도와드릴까요?"):
        self.output_text = output_text
        self.last_request: dict[str, Any] | None = None

    def create(self, **kwargs: Any) -> SimpleNamespace:
        self.last_request = kwargs
        return SimpleNamespace(
            output_text=self.output_text,
            model="gpt-5.6-luna",
            id="resp_test_123",
        )


class FakeOpenAI:
    def __init__(self, output_text: str = "안녕하세요! 무엇을 도와드릴까요?"):
        self.responses = FakeResponses(output_text)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Generator[None, None, None]:
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "FastAPI chatbot backend is running."


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_info_does_not_expose_api_key() -> None:
    response = client.get("/info")

    assert response.status_code == 200
    assert response.json()["app_version"] == "1.0.0"
    assert response.json()["model"] == "gpt-5.6-luna"
    assert response.json()["openai_configured"] is False
    assert "openai_api_key" not in response.json()


def test_example_api_key_placeholder_is_not_treated_as_configured() -> None:
    settings = Settings(
        openai_api_key="replace-with-your-openai-project-api-key"
    )

    assert settings.has_openai_api_key is False


def test_chat_uses_responses_api_with_conversation_history() -> None:
    fake_openai = FakeOpenAI()
    app.dependency_overrides[get_openai_client] = lambda: fake_openai

    response = client.post(
        "/chat",
        json={
            "messages": [
                {"role": "user", "content": "Docker가 뭐야?"},
                {"role": "assistant", "content": "컨테이너 플랫폼입니다."},
                {"role": "user", "content": "한 문장으로 다시 설명해줘."},
            ]
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "안녕하세요! 무엇을 도와드릴까요?",
        "model": "gpt-5.6-luna",
        "response_id": "resp_test_123",
    }

    request = fake_openai.responses.last_request
    assert request is not None
    assert request["model"] == "gpt-5.6-luna"
    assert request["store"] is False
    assert request["input"][-1] == {
        "role": "user",
        "content": "한 문장으로 다시 설명해줘.",
    }
    from app.prompts import CHAT_INSTRUCTIONS
    assert CHAT_INSTRUCTIONS in request["instructions"]


def test_chat_requires_api_key_when_client_is_not_overridden() -> None:
    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "안녕하세요"}]},
    )

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_chat_rejects_blank_message() -> None:
    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "   "}]},
    )

    assert response.status_code == 422


def test_chat_requires_last_message_to_be_user() -> None:
    response = client.post(
        "/chat",
        json={
            "messages": [
                {"role": "user", "content": "안녕"},
                {"role": "assistant", "content": "반갑습니다."},
            ]
        },
    )

    assert response.status_code == 422


def test_chat_rejects_non_alternating_roles() -> None:
    response = client.post(
        "/chat",
        json={
            "messages": [
                {"role": "user", "content": "첫 질문"},
                {"role": "user", "content": "두 번째 질문"},
            ]
        },
    )

    assert response.status_code == 422


def test_chat_rejects_empty_model_output() -> None:
    app.dependency_overrides[get_openai_client] = lambda: FakeOpenAI("   ")

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "안녕하세요"}]},
    )

    assert response.status_code == 502
