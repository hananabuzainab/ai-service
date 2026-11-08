
from app.interview_schemas import InterviewStartRequest
from app.interview_plan_schemas import InterviewPlan
from app.interview_planner import generate_interview_plan


# --------------------------------------------------
# Test data
# --------------------------------------------------

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
                "importance": 0.9,
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

    # Four behavioral questions.
    for question_id in range(1, 5):

        questions.append({
            "id": question_id,
            "category": "behavioral",
            "skill": None,
            "difficulty": "medium",
            "primary_dimension": "communication",
            "secondary_dimensions": ["problem_solving"],
            "evaluation_criteria": [
                "Explains the situation clearly",
                "Describes the actions taken",
            ],
        })

    # Six technical questions.
    for question_id in range(5, 11):

        questions.append({
            "id": question_id,
            "category": "technical",
            "skill": "django",
            "difficulty": "medium",
            "primary_dimension": "technical_depth",
            "secondary_dimensions": ["problem_solving"],
            "evaluation_criteria": [
                "Explains the technical concepts",
                "Provides a practical solution",
            ],
        })

    return {
        "questions": questions,
    }


# --------------------------------------------------
# Tests
# --------------------------------------------------

def test_generate_interview_plan(monkeypatch):

    fake_result = create_plan()

    def fake_ask_llm_json(
        system_prompt,
        user_message,
        response_schema=None,
    ):
        assert response_schema == InterviewPlan
        assert "Software Engineer" in user_message
        assert "django" in user_message
        assert "python" in user_message

        return fake_result

    monkeypatch.setattr(
        "app.interview_planner.ask_llm_json",
        fake_ask_llm_json,
    )

    plan = generate_interview_plan(create_request())

    assert isinstance(plan, InterviewPlan)
    assert len(plan.questions) == 10

    assert sum(
        q.category == "behavioral"
        for q in plan.questions
    ) == 4

    assert sum(
        q.category == "technical"
        for q in plan.questions
    ) == 6

    assert [
        q.id for q in plan.questions
    ] == list(range(1, 11))


def test_reject_invalid_question_distribution(monkeypatch):

    fake_result = create_plan()

    # Change one technical question into behavioral.
    fake_result["questions"][4]["category"] = "behavioral"
    fake_result["questions"][4]["skill"] = None

    def fake_ask_llm_json(*args, **kwargs):
        return fake_result

    monkeypatch.setattr(
        "app.interview_planner.ask_llm_json",
        fake_ask_llm_json,
    )

    import pytest

    with pytest.raises(
        ValueError,
        match="4 behavioral and 6 technical",
    ):
        generate_interview_plan(create_request())


def test_reject_non_sequential_question_ids(monkeypatch):

    fake_result = create_plan()

    fake_result["questions"][0]["id"] = 10

    def fake_ask_llm_json(*args, **kwargs):
        return fake_result

    monkeypatch.setattr(
        "app.interview_planner.ask_llm_json",
        fake_ask_llm_json,
    )

    import pytest

    with pytest.raises(
        ValueError,
        match="sequential from 1 to 10",
    ):
        generate_interview_plan(create_request())
