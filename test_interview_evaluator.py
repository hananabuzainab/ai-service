
import pytest

from app.interview_evaluator import evaluate_interview_answer
from app.interview_schemas import (
    InterviewAnswerRequest,
    InterviewStartRequest,
)
from app.interview_plan_schemas import (
    InterviewPlan,
    PlannedQuestion,
)
from app.interview_generation_schemas import (
    GeneratedQuestions,
    GeneratedQuestion,
)


def create_interview():
    request = InterviewStartRequest(
        interview_id="test-123",
        resume=(
            "Python developer with practical experience in software development, "
            "programming concepts, and building applications using Python."
        ),
        job_description="We need a Python developer with programming skills.",
        job_title="Python Developer",
        matching_skills=[
            {
                "id": 1,
                "name": "Python",
                "category": "languages",
                "importance": 1,
                "candidate_confidence": 0.9,
            }
        ],
        missing_skills=[],
    )

    plan = InterviewPlan(
        questions=[
            PlannedQuestion(
                id=i,
                category="technical",
                skill="Python",
                difficulty="medium",
                primary_dimension="technical_depth",
                secondary_dimensions=["problem_solving"],
                evaluation_criteria=[
                    "Explains the concept correctly.",
                    "Provides a relevant example.",
                ],
            )
            for i in range(1, 11)
        ]
    )

    questions = GeneratedQuestions(
        questions=[
            GeneratedQuestion(
                id=i,
                text="What is the difference between a list and a tuple?",
                type="main",
            )
            for i in range(1, 11)
        ]
    )

    return {
        "request": request,
        "plan": plan,
        "questions": questions,
    }


def test_evaluate_answer_success(monkeypatch):
    interview = create_interview()

    def fake_ask_llm_json(*args, **kwargs):
        return {
            "id": "1",
            "score": 8.5,
            "criteria_results": [
                {
                    "criterion": "Explains the concept correctly.",
                    "status": "met",
                    "evidence": "The candidate correctly explained mutability.",
                },
                {
                    "criterion": "Provides a relevant example.",
                    "status": "partially_met",
                    "evidence": "The candidate explained the difference but did not provide a detailed example.",
                },
            ],
            "better_answer": "A list is mutable, while a tuple is immutable.",
        }

    monkeypatch.setattr(
        "app.interview_evaluator.ask_llm_json",
        fake_ask_llm_json,
    )

    request = InterviewAnswerRequest(
        interview_id="test-123",
        id="1",
        text="A list is mutable, but a tuple is immutable.",
    )

    result = evaluate_interview_answer(request, interview)

    # Check the public response.
    assert result.id == "1"
    assert result.score == 8.5
    assert result.better_answer == (
        "A list is mutable, while a tuple is immutable."
    )

    # Internal evaluation must not be exposed in the public response.
    assert not hasattr(result, "criteria_results")

    # Check that the answer and full evaluation were stored internally.
    assert interview["evaluations"]["1"]["answer"] == request.text

    stored_evaluation = interview["evaluations"]["1"]["evaluation"]

    assert stored_evaluation.score == 8.5
    assert len(stored_evaluation.criteria_results) == 2
    assert stored_evaluation.criteria_results[0].status == "met"
    assert (
        stored_evaluation.criteria_results[0].evidence
        == "The candidate correctly explained mutability."
    )


def test_evaluate_answer_question_not_found(monkeypatch):
    interview = create_interview()

    request = InterviewAnswerRequest(
        interview_id="test-123",
        id="11",
        text="My answer.",
    )

    with pytest.raises(ValueError, match="Question not found"):
        evaluate_interview_answer(request, interview)


def test_evaluate_answer_id_mismatch(monkeypatch):
    interview = create_interview()

    def fake_ask_llm_json(*args, **kwargs):
        return {
            "id": "2",
            "score": 8,
            "criteria_results": [
                {
                    "criterion": "Explains the concept correctly.",
                    "status": "met",
                    "evidence": "The candidate explained the concept.",
                },
                {
                    "criterion": "Provides a relevant example.",
                    "status": "met",
                    "evidence": "The candidate provided an example.",
                },
            ],
            "better_answer": "A model answer.",
        }

    monkeypatch.setattr(
        "app.interview_evaluator.ask_llm_json",
        fake_ask_llm_json,
    )

    request = InterviewAnswerRequest(
        interview_id="test-123",
        id="1",
        text="My answer.",
    )

    with pytest.raises(ValueError, match="question ID does not match"):
        evaluate_interview_answer(request, interview)

    # An invalid evaluation must not be stored.
    assert "evaluations" not in interview
