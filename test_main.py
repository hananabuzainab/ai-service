
import pytest

from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_extract_resume_success(monkeypatch):
    extracted_text = (
        "Computer Engineer with experience in Python, "
        "Django, SQL, PostgreSQL and machine learning."
    )

    expected_skills = [
        {
            "name": "python",
            "category": "languages",
            "confidence_score": 0.95,
        }
    ]

    monkeypatch.setattr(
        main,
        "extract_text_from_bytes",
        lambda data, filename: extracted_text,
    )

    monkeypatch.setattr(
        main,
        "extract_skills_from_text",
        lambda *args: expected_skills,
    )

    response = client.post(
        "/v1/extract-resume",
        files={
            "file": (
                "resume.txt",
                b"sample resume content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["extracted_text"] == extracted_text
    assert data["skills"] == expected_skills


def test_extract_resume_file_too_large():
    response = client.post(
        "/v1/extract-resume",
        files={
            "file": (
                "resume.txt",
                b"A" * (main.MAX_SIZE + 1),
                "text/plain",
            )
        },
    )

    assert response.status_code == 422

    data = response.json()

    assert data["detail"]["error"]["code"] == "FILE_TOO_LARGE"


def test_extract_resume_invalid_file(monkeypatch):
    from app.pdf_utils import ResumeError

    def fake_extract(data, filename):
        raise ResumeError(
            "NO_TEXT",
            "No readable text found."
        )

    monkeypatch.setattr(
        main,
        "extract_text_from_bytes",
        fake_extract,
    )

    response = client.post(
        "/v1/extract-resume",
        files={
            "file": (
                "resume.pdf",
                b"%PDF fake content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422

    data = response.json()

    assert data["detail"]["error"]["code"] == "NO_TEXT"


def test_extract_job_success(monkeypatch):
    expected_skills = [
        {
            "name": "python",
            "category": "languages",
            "importance": 0.9,
        }
    ]

    monkeypatch.setattr(
        main,
        "extract_skills_from_text",
        lambda *args: expected_skills,
    )

    response = client.post(
        "/v1/extract-job",
        json={
            "text": (
                "We need a Python developer with experience "
                "in Django and PostgreSQL databases."
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["skills"] == expected_skills


def test_extract_job_short_text_rejected():
    response = client.post(
        "/v1/extract-job",
        json={
            "text": "Python developer"
        },
    )

    assert response.status_code == 422


def test_extract_job_ai_failure(monkeypatch):
    def fake_extract(*args):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "code": "AI_FAILED",
                    "message": "Could not extract skills.",
                }
            },
        )

    monkeypatch.setattr(
        main,
        "extract_skills_from_text",
        fake_extract,
    )

    response = client.post(
        "/v1/extract-job",
        json={
            "text": (
                "We need a Python developer with experience "
                "in Django and PostgreSQL databases."
            )
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"]["error"]["code"] == "AI_FAILED"
