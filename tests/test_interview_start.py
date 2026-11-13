
from fastapi.testclient import TestClient

from app.main import app, interviews
from app.interview_plan_schemas import InterviewPlan
from app.interview_generation_schemas import GeneratedQuestions


client = TestClient(app)


def create_request():
    return {
        "interview_id": 123,
        "resume": "Candidate resume text " * 10,
        "job_description": "Software Engineer job description " * 10,
        "job_title": "Software Engineer",
        "matching_skills": [
            {
                "id": 1,
                "name": "python",
                "category": "languages",
                "importance": 1.0,
                "candidate_confidence": 0.9,
            }
        ],
        "missing_skills": [
            {
                "id": 2,
                "name": "django",
                "category": "frameworks",
                "importance": 0.95,
            }
        ],
    }


def create_plan():
    questions = []

    for i in range(1, 11):
        category = "behavioral" if i <= 4 else "technical"

        questions.append({
            "id": i,
            "category": category,
            "skill": None if category == "behavioral" else "django",
            "difficulty": "medium",
            "primary_dimension": (
                "communication"
                if category == "behavioral"
                else "technical_depth"
            ),
            "secondary_dimensions": [],
            "evaluation_criteria": [
                "Explains the approach clearly",
                "Provides relevant details",
            ],
        })

    return InterviewPlan(questions=questions)


def create_generated_questions():
    return GeneratedQuestions(
        questions=[
            {
                "id": i,
                "text": f"Interview question number {i}?",
                "type": "main",
            }
            for i in range(1, 11)
        ]
    )


def test_start_interview(monkeypatch):

    interviews.clear()

    def fake_generate_plan(req):
        return create_plan()

    def fake_generate_questions(req, plan):
        assert isinstance(plan, InterviewPlan)
        return create_generated_questions()

    monkeypatch.setattr(
        "app.main.generate_interview_plan",
        fake_generate_plan,
    )

    monkeypatch.setattr(
        "app.main.generate_interview_questions",
        fake_generate_questions,
    )

    response = client.post(
        "/v1/interview/start",
        json=create_request(),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["questions"]) == 10

    assert data["questions"][0] == {
        "id": 1,
        "text": "Interview question number 1?",
        "type": "main",
    }

    assert all(
        question["type"] == "main"
        for question in data["questions"]
    )

    # Ensure interview data was stored.
    assert 123 in interviews

    saved = interviews[123]

    assert isinstance(saved["plan"], InterviewPlan)
    assert isinstance(saved["questions"], GeneratedQuestions)


def test_start_interview_invalid_request():

    response = client.post(
        "/v1/interview/start",
        json={
            "interview_id": "test-123",
        },
    )

    assert response.status_code == 422
