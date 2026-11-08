
import pytest

from app.interview_question_generator import generate_interview_questions
from app.interview_schemas import InterviewStartRequest
from app.interview_plan_schemas import InterviewPlan
from app.interview_generation_schemas import GeneratedQuestions


def create_request():
    return InterviewStartRequest(
        interview_id="test-123",
        resume="Candidate resume text " * 10,
        job_description="Software Engineer job description " * 10,
        job_title="Software Engineer",
        matching_skills=[
            {
                "id": 1,
                "name": "python",
                "category": "languages",
                "importance": 1.0,
                "candidate_confidence": 0.9,
            }
        ],
        missing_skills=[
            {
                "id": 2,
                "name": "django",
                "category": "frameworks",
                "importance": 0.95,
            }
        ],
    )


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
    return {
        "questions": [
            {
                "id": i,
                "text": f"Interview question number {i}?",
                "type": "main",
            }
            for i in range(1, 11)
        ]
    }


def test_generate_interview_questions(monkeypatch):

    fake_result = create_generated_questions()

    def fake_ask_llm_json(
        system_prompt,
        user_message,
        response_schema=None,
    ):
        assert response_schema == GeneratedQuestions
        assert "Software Engineer" in user_message
        assert "django" in user_message
        assert "Candidate resume text" in user_message

        return fake_result

    monkeypatch.setattr(
        "app.interview_question_generator.ask_llm_json",
        fake_ask_llm_json,
    )

    generated = generate_interview_questions(
        create_request(),
        create_plan(),
    )

    assert len(generated.questions) == 10

    assert [q.id for q in generated.questions] == list(range(1, 11))

    assert all(q.type == "main" for q in generated.questions)


def test_reject_mismatched_question_ids(monkeypatch):

    fake_result = create_generated_questions()

    # Change the first question ID.
    fake_result["questions"][0]["id"] = 10

    def fake_ask_llm_json(*args, **kwargs):
        return fake_result

    monkeypatch.setattr(
        "app.interview_question_generator.ask_llm_json",
        fake_ask_llm_json,
    )

    with pytest.raises(
        ValueError,
        match="IDs must match the interview plan",
    ):
        generate_interview_questions(
            create_request(),
            create_plan(),
        )


def test_reject_follow_up_questions(monkeypatch):

    fake_result = create_generated_questions()

    # Change one question type.
    fake_result["questions"][0]["type"] = "follow_up"

    def fake_ask_llm_json(*args, **kwargs):
        return fake_result

    monkeypatch.setattr(
        "app.interview_question_generator.ask_llm_json",
        fake_ask_llm_json,
    )

    with pytest.raises(
        ValueError,
        match="type 'main'",
    ):
        generate_interview_questions(
            create_request(),
            create_plan(),
        )
