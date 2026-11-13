
import pytest

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import main
from app.final_report_schemas import FinalReportResponse


client = TestClient(main.app)


# --------------------------------------------------
# Health check
# --------------------------------------------------

def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --------------------------------------------------
# Resume extraction
# --------------------------------------------------

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


# --------------------------------------------------
# Job extraction
# --------------------------------------------------

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
    from fastapi import HTTPException

    def fake_extract(*args):
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


# --------------------------------------------------
# Final report test data
# --------------------------------------------------

def create_final_report_request(interview_id):
    return {
        "interview_id": interview_id,
        "resume_text": (
            "Computer Engineer with experience in Python, "
            "Django, SQL, machine learning and databases."
        ),
        "job_description": (
            "We are looking for a Python developer "
            "with experience in backend development."
        ),
        "questions": [
            {
                "question_id": i,
                "sequence_number": i,
                "question": f"Question {i}",
                "answer": f"Candidate answer {i}",
                "score": 8.5,
                "better_answer": f"Better answer {i}",
            }
            for i in range(1, 11)
        ],
    }


def create_final_report_response(interview_id):
    return FinalReportResponse(
        interview_id=interview_id,
        interview_summary={
            "summary": "The candidate demonstrated good performance.",
            "strengths": [
                "Good Python knowledge.",
                "Clear communication.",
            ],
            "job_relevance": "The candidate's skills are relevant to the role.",
        },
        improvement_areas=[
            {
                "area": "Problem solving",
                "recommendation": "Practice more practical coding problems.",
            }
        ],
        dimension_scores=[
            {
                "dimension": "technical_depth",
                "score": 4,
                "evidence": "Demonstrated good technical knowledge.",
            },
            {
                "dimension": "communication",
                "score": 4,
                "evidence": "Provided clear explanations.",
            },
            {
                "dimension": "domain_experience",
                "score": 3,
                "evidence": "Showed some relevant domain knowledge.",
            },
            {
                "dimension": "problem_solving",
                "score": 4,
                "evidence": "Explained a reasonable problem-solving approach.",
            },
        ],
        discrepancy_flags=[],
    )


# --------------------------------------------------
# Final report endpoint tests
# --------------------------------------------------

def test_generate_final_report_success(monkeypatch):
    interview_id = 1001

    monkeypatch.setitem(
        main.interviews,
        interview_id,
        {},
    )

    expected_report = create_final_report_response(interview_id)

    monkeypatch.setattr(
        main,
        "generate_final_report",
        lambda req, interview: expected_report,
    )

    response = client.post(
        "/v1/interview/report",
        json=create_final_report_request(interview_id),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["interview_id"] == interview_id
    assert len(data["dimension_scores"]) == 4
    assert data["discrepancy_flags"] == []


def test_generate_final_report_interview_not_found():
    response = client.post(
        "/v1/interview/report",
        json=create_final_report_request(2001),
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]["error"]["code"]
        == "INTERVIEW_CONTEXT_NOT_FOUND"
    )


def test_generate_final_report_missing_evaluation():
    interview_id = 1002

    monkeypatch_interview = {
        "evaluations": {},
    }

    from app.final_report_generator import generate_final_report

    # Use the actual generator to test missing evaluations.
    original_interviews = main.interviews.copy()

    try:
        main.interviews[interview_id] = monkeypatch_interview

        response = client.post(
            "/v1/interview/report",
            json=create_final_report_request(interview_id),
        )

    finally:
        main.interviews.clear()
        main.interviews.update(original_interviews)

    assert response.status_code == 400

    assert (
        response.json()["detail"]["error"]["code"]
        == "INVALID_INTERVIEW_DATA"
    )


def test_generate_final_report_answer_mismatch():
    interview_id = 1003

    evaluations = {}

    for question_id in range(1, 11):
        evaluations[question_id] = {
            "answer": (
                "Different answer"
                if question_id == 1
                else f"Candidate answer {question_id}"
            ),
            "evaluation": SimpleNamespace(
                score=8.5,
                better_answer=f"Better answer {question_id}",
            ),
        }

    interview = {
        "evaluations": evaluations,
    }

    original_interviews = main.interviews.copy()

    try:
        main.interviews[interview_id] = interview

        response = client.post(
            "/v1/interview/report",
            json=create_final_report_request(interview_id),
        )

    finally:
        main.interviews.clear()
        main.interviews.update(original_interviews)

    assert response.status_code == 400

    assert (
        response.json()["detail"]["error"]["code"]
        == "INVALID_INTERVIEW_DATA"
    )


def test_generate_final_report_ai_failure(monkeypatch):
    interview_id = 1004

    monkeypatch.setitem(
        main.interviews,
        interview_id,
        {},
    )

    def fake_generate_report(req, interview):
        raise RuntimeError("Gemini service unavailable.")

    monkeypatch.setattr(
        main,
        "generate_final_report",
        fake_generate_report,
    )

    response = client.post(
        "/v1/interview/report",
        json=create_final_report_request(interview_id),
    )

    assert response.status_code == 502

    assert (
        response.json()["detail"]["error"]["code"]
        == "AI_FAILED"
    )

# --------------------------------------------------
# Delete interview endpoint tests
# --------------------------------------------------

def test_delete_interview_success():
    interview_id = 3001

    main.interviews[interview_id] = {
        "request": {},
        "plan": {},
        "questions": {},
        "evaluations": {},
    }

    response = client.delete(
        f"/v1/interview/{interview_id}"
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Interview data deleted successfully."
    }

    assert interview_id not in main.interviews


def test_delete_interview_not_found():
    interview_id = 3002

    main.interviews.pop(interview_id, None)

    response = client.delete(
        f"/v1/interview/{interview_id}"
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Interview data deleted successfully."
    }


def test_delete_interview_repeated_request():
    interview_id = 3003

    main.interviews[interview_id] = {
        "request": {},
        "plan": {},
        "questions": {},
        "evaluations": {},
    }

    first_response = client.delete(
        f"/v1/interview/{interview_id}"
    )

    second_response = client.delete(
        f"/v1/interview/{interview_id}"
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert interview_id not in main.interviews
