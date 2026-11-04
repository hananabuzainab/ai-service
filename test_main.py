
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

from types import SimpleNamespace


def test_interview_next_question_generation_failure(monkeypatch):

    interview_id = "test-interview-001"

    current_question = {
        "question_id": 1,
        "question": "Explain how you solve a technical problem.",
        "is_follow_up": False,
        "follow_up_used": False,
    }

    # Prepare a test interview without calling Gemini
    interview = {
        "answers": [],
        "follow_up_count": 0,
        "processed_requests": {},
        "plan": {
            "questions": [
                {"question_id": 1},
                {"question_id": 2},
            ]
        },
        "current_question": current_question.copy(),
    }

    monkeypatch.setitem(
        main.interviews,
        interview_id,
        interview,
    )

    # Simulate successful answer evaluation
    evaluation = SimpleNamespace(
        needs_follow_up=False,
        follow_up_reason=None,
        model_dump=lambda: {
            "needs_follow_up": False,
            "follow_up_reason": None,
            "criteria_results": [],
            "strengths": [],
            "improvements": [],
        },
    )

    monkeypatch.setattr(
        main,
        "evaluate_interview_answer",
        lambda *args: evaluation,
    )

    # First attempt: simulate Gemini failure
    def fake_generate_question(*args):
        raise RuntimeError("Simulated Gemini failure")

    monkeypatch.setattr(
        main,
        "generate_interview_question",
        fake_generate_question,
    )

    request_data = {
        "interview_id": interview_id,
        "question_id": 1,
        "request_id": "request-001",
        "answer": "I used Python to solve a technical problem.",
    }

    response = client.post(
        "/v1/interview/answer",
        json=request_data,
    )

    # Verify the API reports the AI failure
    assert response.status_code == 502
    assert response.json()["detail"]["error"]["code"] == "AI_FAILED"

    # Verify the answer was not saved
    assert interview["answers"] == []

    # Verify the current question was not changed
    assert interview["current_question"] == current_question

    # Verify the failed request was not cached
    assert "request-001" not in interview["processed_requests"]

    # Second attempt: simulate successful question generation
    monkeypatch.setattr(
        main,
        "generate_interview_question",
        lambda *args: SimpleNamespace(
            question="How would you optimize a slow database query?"
        ),
    )

    response = client.post(
        "/v1/interview/answer",
        json=request_data,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["next_question_id"] == 2
    assert data["question"] == "How would you optimize a slow database query?"

    # Verify the answer was saved exactly once
    assert len(interview["answers"]) == 1

    # Verify the interview moved to question 2
    assert interview["current_question"]["question_id"] == 2    
def test_interview_follow_up_generation_failure(monkeypatch):

    interview_id = "test-follow-up-001"

    current_question = {
        "question_id": 1,
        "question": "Describe a technical challenge you faced.",
        "is_follow_up": False,
        "follow_up_used": False,
    }

    interview = {
        "answers": [],
        "follow_up_count": 0,
        "processed_requests": {},
        "plan": {
            "questions": [
                {"question_id": 1},
                {"question_id": 2},
            ]
        },
        "current_question": current_question.copy(),
    }

    monkeypatch.setitem(
        main.interviews,
        interview_id,
        interview,
    )

    # Simulate an evaluation that requires a follow-up
    evaluation = SimpleNamespace(
        needs_follow_up=True,
        follow_up_reason="The answer needs more details.",
        model_dump=lambda: {
            "needs_follow_up": True,
            "follow_up_reason": "The answer needs more details.",
            "criteria_results": [],
            "strengths": [],
            "improvements": [],
        },
    )

    monkeypatch.setattr(
        main,
        "evaluate_interview_answer",
        lambda *args: evaluation,
    )

    # First attempt: simulate follow-up generation failure
    def fake_generate_follow_up(*args):
        raise RuntimeError("Simulated Gemini failure")

    monkeypatch.setattr(
        main,
        "generate_follow_up_question",
        fake_generate_follow_up,
    )

    request_data = {
        "interview_id": interview_id,
        "question_id": 1,
        "request_id": "follow-up-request-001",
        "answer": "I faced a database performance problem.",
    }

    response = client.post(
        "/v1/interview/answer",
        json=request_data,
    )

    assert response.status_code == 502
    assert response.json()["detail"]["error"]["code"] == "AI_FAILED"

    # Verify that nothing was saved after failure
    assert interview["answers"] == []
    assert interview["follow_up_count"] == 0
    assert interview["current_question"] == current_question
    assert "follow-up-request-001" not in interview["processed_requests"]

    # Second attempt: simulate successful follow-up generation
    monkeypatch.setattr(
        main,
        "generate_follow_up_question",
        lambda *args: SimpleNamespace(
            question="Can you explain how you identified the database issue?"
        ),
    )

    response = client.post(
        "/v1/interview/answer",
        json=request_data,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_follow_up"] is True
    assert data["question"] == (
        "Can you explain how you identified the database issue?"
    )

    # Verify that the answer was saved exactly once
    assert len(interview["answers"]) == 1

    # Verify follow-up state
    assert interview["follow_up_count"] == 1
    assert interview["current_question"]["is_follow_up"] is True
    assert interview["current_question"]["follow_up_used"] is True
def test_interview_final_evaluation_failure(monkeypatch):

    interview_id = "test-final-evaluation-001"

    current_question = {
        "question_id": 1,
        "question": "Explain a technical problem you solved.",
        "is_follow_up": False,
        "follow_up_used": False,
    }

    interview = {
        "job_title": "Backend Developer",
        "job_description": "Junior Backend Developer position.",
        "resume_text": "Computer Engineering graduate.",
        "matching_skills": [],
        "missing_skills": [],
        "answers": [],
        "follow_up_count": 0,
        "processed_requests": {},
        "plan": {
            "questions": [
                {"question_id": 1},
            ]
        },
        "current_question": current_question.copy(),
        "status": "in_progress",
    }

    monkeypatch.setitem(
        main.interviews,
        interview_id,
        interview,
    )

    evaluation = SimpleNamespace(
        needs_follow_up=False,
        follow_up_reason=None,
        model_dump=lambda: {
            "needs_follow_up": False,
            "follow_up_reason": None,
            "criteria_results": [],
            "strengths": [],
            "improvements": [],
        },
    )

    monkeypatch.setattr(
        main,
        "evaluate_interview_answer",
        lambda *args: evaluation,
    )

    # First attempt: simulate final evaluation failure
    def fake_final_evaluation(*args):
        raise RuntimeError("Simulated Gemini failure")

    monkeypatch.setattr(
        main,
        "evaluate_final_interview",
        fake_final_evaluation,
    )

    request_data = {
        "interview_id": interview_id,
        "question_id": 1,
        "request_id": "final-request-001",
        "answer": "I used Python to solve a technical problem.",
    }

    response = client.post(
        "/v1/interview/answer",
        json=request_data,
    )

    assert response.status_code == 502
    assert response.json()["detail"]["error"]["code"] == "AI_FAILED"

    # Verify the answer was rolled back
    assert interview["answers"] == []

    # Verify the interview was not completed
    assert interview["current_question"] == current_question
    assert interview["status"] == "in_progress"
    assert "final_evaluation" not in interview

    # Verify the failed request was not cached
    assert "final-request-001" not in interview["processed_requests"]

    # Second attempt: simulate successful final evaluation
    final_evaluation = SimpleNamespace(
        model_dump=lambda: {
            "overall_score": 85,
            "summary": "Good interview performance.",
        },
    )

    monkeypatch.setattr(
        main,
        "evaluate_final_interview",
        lambda *args: final_evaluation,
    )

    response = client.post(
        "/v1/interview/answer",
        json=request_data,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["interview_completed"] is True
    assert data["final_evaluation"]["overall_score"] == 85

    # Verify the answer was saved exactly once
    assert len(interview["answers"]) == 1

    # Verify the interview was completed
    assert interview["current_question"] is None
    assert interview["status"] == "completed"
    assert "final_evaluation" in interview

    # Verify the successful request was cached
    assert "final-request-001" in interview["processed_requests"]    


def test_full_interview_success(monkeypatch):
    # 1. Prepare a two-question interview plan
    plan = SimpleNamespace(
        model_dump=lambda: {
            "questions": [
                {"question_id": 1},
                {"question_id": 2},
            ]
        }
    )

    monkeypatch.setattr(
        main,
        "create_interview_plan",
        lambda *args: plan,
    )

    # 2. Generate the first and second main questions
    questions = iter([
        "Tell me about a technical challenge you solved.",
        "How do you work with databases?",
    ])

    monkeypatch.setattr(
        main,
        "generate_interview_question",
        lambda *args: SimpleNamespace(question=next(questions)),
    )

    # 3. Prepare three evaluations:
    # First answer needs follow-up.
    # Second and third answers do not.
    evaluations = iter([
        (True, "More details are needed."),
        (False, None),
        (False, None),
    ])

    def fake_evaluate(*args):
        needs_follow_up, reason = next(evaluations)

        return SimpleNamespace(
            needs_follow_up=needs_follow_up,
            follow_up_reason=reason,
            model_dump=lambda: {
                "needs_follow_up": needs_follow_up,
                "follow_up_reason": reason,
                "criteria_results": [],
                "strengths": [],
                "improvements": [],
            },
        )

    monkeypatch.setattr(
        main,
        "evaluate_interview_answer",
        fake_evaluate,
    )

    # 4. Generate a follow-up question
    monkeypatch.setattr(
        main,
        "generate_follow_up_question",
        lambda *args: SimpleNamespace(
            question="Can you explain more about your solution?"
        ),
    )

    # 5. Prepare the final evaluation
    monkeypatch.setattr(
        main,
        "evaluate_final_interview",
        lambda *args: SimpleNamespace(
            model_dump=lambda: {
                "overall_score": 85,
                "summary": "Good interview performance.",
            }
        ),
    )

    # 6. Start the interview
    start_response = client.post(
        "/v1/interview/start",
        json={
            "job_title": "Backend Developer",
            "job_description": (
                "Junior Backend Developer with Python experience."
            ),
            "resume_text": "Computer Engineering graduate.",
            "matching_skills": [],
            "missing_skills": [],
        },
    )

    assert start_response.status_code == 200

    start_data = start_response.json()
    interview_id = start_data["interview_id"]

    assert start_data["question_id"] == 1
    assert start_data["question"] == (
        "Tell me about a technical challenge you solved."
    )

    # 7. Submit the first answer
    response = client.post(
        "/v1/interview/answer",
        json={
            "interview_id": interview_id,
            "question_id": 1,
            "request_id": "full-test-001",
            "answer": "I solved a performance issue using Python.",
        },
    )

    assert response.status_code == 200
    assert response.json()["is_follow_up"] is True
    assert response.json()["question"] == (
        "Can you explain more about your solution?"
    )

    # 8. Answer the follow-up question
    response = client.post(
        "/v1/interview/answer",
        json={
            "interview_id": interview_id,
            "question_id": 1,
            "request_id": "full-test-002",
            "answer": "I optimized the code and reduced execution time.",
        },
    )

    assert response.status_code == 200
    assert response.json()["next_question_id"] == 2
    assert response.json()["question"] == (
        "How do you work with databases?"
    )

    # 9. Answer the second main question
    response = client.post(
        "/v1/interview/answer",
        json={
            "interview_id": interview_id,
            "question_id": 2,
            "request_id": "full-test-003",
            "answer": "I use SQL to query and manage databases.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    # 10. Verify interview completion
    assert data["interview_completed"] is True
    assert data["final_evaluation"]["overall_score"] == 85

    interview = main.interviews[interview_id]

    assert len(interview["answers"]) == 3
    assert interview["current_question"] is None
    assert interview["status"] == "completed"
    assert "final_evaluation" in interview
