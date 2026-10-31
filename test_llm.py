
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


def test_invalid_json_retries(monkeypatch):
    responses = [
        Mock(text="invalid json"),
        Mock(text='{"skills": []}')
    ]

    calls = []

    def fake_generate(*args, **kwargs):
        calls.append(1)
        return responses.pop(0)

    monkeypatch.setattr(
        llm,
        "_generate_response",
        fake_generate
    )

    result = llm.ask_llm_json(
        "system prompt",
        "user message",
        retries=1
    )

    assert result == {"skills": []}
    assert len(calls) == 2


def test_empty_response_retries(monkeypatch):
    responses = [
        Mock(text=None),
        Mock(text='{"skills": []}')
    ]

    monkeypatch.setattr(
        llm,
        "_generate_response",
        lambda *args, **kwargs: responses.pop(0)
    )

    result = llm.ask_llm_json(
        "system prompt",
        "user message",
        retries=1
    )

    assert result == {"skills": []}


def test_non_object_json_retries(monkeypatch):
    responses = [
        Mock(text='["python", "django"]'),
        Mock(text='{"skills": []}')
    ]

    monkeypatch.setattr(
        llm,
        "_generate_response",
        lambda *args, **kwargs: responses.pop(0)
    )

    result = llm.ask_llm_json(
        "system prompt",
        "user message",
        retries=1
    )

    assert result == {"skills": []}


def test_invalid_retries_value():
    with pytest.raises(ValueError):
        llm.ask_llm_json(
            "system prompt",
            "user message",
            retries=-1
        )


def test_boolean_retries_rejected():
    with pytest.raises(ValueError):
        llm.ask_llm_json(
            "system prompt",
            "user message",
            retries=True
        )


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

    with pytest.raises(RuntimeError):
        llm.ask_llm_json(
            "system prompt",
            "user message",
            retries=2
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
