
from unittest.mock import Mock

import pytest

from app import llm


def test_valid_json_response(monkeypatch):
    response = Mock()
    response.text = '{"skills": []}'

    monkeypatch.setattr(
        llm,
        "_generate_response",
        lambda *args, **kwargs: response
    )

    result = llm.ask_llm_json(
        "system prompt",
        "user message"
    )

    assert result == {"skills": []}


def test_invalid_json_no_retry(monkeypatch):
    calls = []

    def fake_generate(*args, **kwargs):
        calls.append(1)
        return Mock(text="invalid json")

    monkeypatch.setattr(
        llm,
        "_generate_response",
        fake_generate
    )

    with pytest.raises(ValueError, match="invalid JSON"):
        llm.ask_llm_json(
            "system prompt",
            "user message"
        )

    assert len(calls) == 1


def test_empty_response_no_retry(monkeypatch):
    calls = []

    def fake_generate(*args, **kwargs):
        calls.append(1)
        return Mock(text=None)

    monkeypatch.setattr(
        llm,
        "_generate_response",
        fake_generate
    )

    with pytest.raises(ValueError, match="empty response"):
        llm.ask_llm_json(
            "system prompt",
            "user message"
        )

    assert len(calls) == 1


def test_non_object_json_no_retry(monkeypatch):
    calls = []

    def fake_generate(*args, **kwargs):
        calls.append(1)
        return Mock(text='["python", "django"]')

    monkeypatch.setattr(
        llm,
        "_generate_response",
        fake_generate
    )

    with pytest.raises(ValueError, match="must be an object"):
        llm.ask_llm_json(
            "system prompt",
            "user message"
        )

    assert len(calls) == 1


def test_permanent_api_error_is_not_retried(monkeypatch):
    calls = []

    def fake_generate(*args, **kwargs):
        calls.append(1)
        raise RuntimeError("API key invalid")

    monkeypatch.setattr(
        llm,
        "_generate_response",
        fake_generate
    )

    with pytest.raises(RuntimeError, match="API key invalid"):
        llm.ask_llm_json(
            "system prompt",
            "user message"
        )

    assert len(calls) == 1


def test_response_schema_is_forwarded(monkeypatch):
    response = Mock()
    response.text = '{"skills": []}'

    received = {}

    def fake_generate(*args, **kwargs):
        received.update(kwargs)
        return response

    monkeypatch.setattr(
        llm,
        "_generate_response",
        fake_generate
    )

    schema = {"type": "OBJECT"}

    llm.ask_llm_json(
        "system prompt",
        "user message",
        response_schema=schema
    )

    assert received["response_schema"] == schema


def test_text_response(monkeypatch):
    response = Mock()
    response.text = "Hello"

    monkeypatch.setattr(
        llm,
        "_generate_response",
        lambda *args, **kwargs: response
    )

    result = llm.ask_llm(
        "system prompt",
        "user message"
    )

    assert result == "Hello"
