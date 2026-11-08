from fastapi.testclient import TestClient

from app.main import app, interviews


client = TestClient(app)


def test_evaluate_answer_success(monkeypatch):
    interview_id = "test-interview"

    interviews[interview_id] = {
        "request": None,
        "plan": None,
        "questions": None,
    }

    def fake_evaluate(req, interview):
        return {
            "id": req.id,
            "score": 8.5,
            "better_answer": "A detailed model answer.",
        }

    monkeypatch.setattr(
        "app.main.evaluate_interview_answer",
        fake_evaluate,
    )

    response = client.post(
        "/v1/interview/answer",
        json={
            "interview_id": interview_id,
            "id": "1",
            "text": "My answer to the question.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == "1"
    assert data["score"] == 8.5
    assert data["better_answer"] == "A detailed model answer."

    interviews.pop(interview_id, None)


def test_evaluate_answer_interview_not_found():
    response = client.post(
        "/v1/interview/answer",
        json={
            "interview_id": "unknown-interview",
            "id": "1",
            "text": "My answer.",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error"]["code"] == "INTERVIEW_NOT_FOUND"


def test_evaluate_answer_invalid_question(monkeypatch):
    interview_id = "test-interview"

    interviews[interview_id] = {}

    def fake_evaluate(req, interview):
        raise ValueError("Question not found in interview plan.")

    monkeypatch.setattr(
        "app.main.evaluate_interview_answer",
        fake_evaluate,
    )

    response = client.post(
        "/v1/interview/answer",
        json={
            "interview_id": interview_id,
            "id": "11",
            "text": "My answer.",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "INVALID_QUESTION"

    interviews.pop(interview_id, None)


def test_evaluate_answer_ai_failure(monkeypatch):
    interview_id = "test-interview"

    interviews[interview_id] = {}

    def fake_evaluate(req, interview):
        raise RuntimeError("Gemini failed.")

    monkeypatch.setattr(
        "app.main.evaluate_interview_answer",
        fake_evaluate,
    )

    response = client.post(
        "/v1/interview/answer",
        json={
            "interview_id": interview_id,
            "id": "1",
            "text": "My answer.",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"]["error"]["code"] == "AI_FAILED"

    interviews.pop(interview_id, None)


def test_evaluate_answer_invalid_request():
    response = client.post(
        "/v1/interview/answer",
        json={
            "interview_id": "",
            "id": "1",
            "text": "My answer.",
        },
    )

    assert response.status_code == 422