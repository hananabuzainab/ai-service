
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.final_report_generator import generate_final_report
from app.final_report_schemas import FinalReportRequest, FinalReportResponse
from app.interview_generation_schemas import GeneratedQuestions


def create_request():
    return SimpleNamespace(
        interview_id=1001,
        resume_text=(
            "Computer Engineer with experience in Python, "
            "Django, SQL, machine learning and databases."
        ),
        job_description=(
            "We are looking for a Python developer "
            "with experience in backend development."
        ),
        questions=[
            SimpleNamespace(
                question_id=i,
                sequence_number=i,
                question=f"Question {i}",
                answer=f"Candidate answer {i}",
                score=8.5,
                better_answer=f"Better answer {i}",
            )
            for i in range(1, 11)
        ],
    )


def create_interview():
    evaluations = {}

    for question_id in range(1, 11):
        evaluations[question_id] = {
            "answer": f"Candidate answer {question_id}",
            "evaluation": SimpleNamespace(
                score=8.5,
                better_answer=f"Better answer {question_id}",
                criteria_results=[],
            ),
        }

    planned_questions = [
        SimpleNamespace(
            id=i,
            category="technical",
            skill="Python",
            difficulty="medium",
            primary_dimension="technical_depth",
            secondary_dimensions=["problem_solving"],
            evaluation_criteria=[
                "Technical accuracy",
                "Clarity of explanation",
            ],
        )
        for i in range(1, 11)
    ]

    return {
        "evaluations": evaluations,
        "plan": SimpleNamespace(questions=planned_questions),
        "questions": GeneratedQuestions(
            questions=[
                {
                    "id": i,
                    "text": f"Question {i}",
                    "type": "main",
                }
                for i in range(1, 11)
            ]
        ),
    }


def create_expected_result():
    return {
        "interview_id": 1001,
        "interview_summary": {
            "summary": "Good interview performance.",
            "strengths": ["Python knowledge"],
            "job_relevance": "Relevant to the job.",
        },
        "improvement_areas": [],
        "dimension_scores": [
            {
                "dimension": "technical_depth",
                "score": 4,
                "evidence": "Good technical knowledge.",
            },
            {
                "dimension": "communication",
                "score": 4,
                "evidence": "Clear explanations.",
            },
            {
                "dimension": "domain_experience",
                "score": 3,
                "evidence": "Some relevant experience.",
            },
            {
                "dimension": "problem_solving",
                "score": 4,
                "evidence": "Reasonable approach.",
            },
        ],
        "discrepancy_flags": [],
    }


def test_generate_final_report_success(monkeypatch):
    request = create_request()
    interview = create_interview()

    expected_result = create_expected_result()

    monkeypatch.setattr(
        "app.final_report_generator.ask_llm_json",
        lambda *args, **kwargs: expected_result,
    )

    result = generate_final_report(request, interview)

    assert result.interview_id == request.interview_id
    assert len(result.dimension_scores) == 4
    assert result.discrepancy_flags == []


def test_generate_final_report_missing_evaluation():
    request = create_request()
    interview = create_interview()

    interview["evaluations"].pop(10)

    with pytest.raises(
        ValueError,
        match="All 10 interview questions must be evaluated.",
    ):
        generate_final_report(request, interview)


def test_generate_final_report_answer_mismatch():
    request = create_request()
    interview = create_interview()

    interview["evaluations"][1]["answer"] = "Different answer"

    with pytest.raises(
        ValueError,
        match="Answer mismatch for question 1.",
    ):
        generate_final_report(request, interview)


def test_generate_final_report_evaluation_mismatch():
    request = create_request()
    interview = create_interview()

    interview["evaluations"][1]["evaluation"].score = 7.0

    with pytest.raises(
        ValueError,
        match="Evaluation mismatch for question 1.",
    ):
        generate_final_report(request, interview)


def test_generate_final_report_missing_planned_question():
    request = create_request()
    interview = create_interview()

    interview["plan"].questions.pop(0)

    with pytest.raises(
        ValueError,
        match="Question 1 not found in interview plan.",
    ):
        generate_final_report(request, interview)


def test_generate_final_report_wrong_interview_id(monkeypatch):
    request = create_request()
    interview = create_interview()

    wrong_result = create_expected_result()
    wrong_result["interview_id"] = 9999

    monkeypatch.setattr(
        "app.final_report_generator.ask_llm_json",
        lambda *args, **kwargs: wrong_result,
    )

    with pytest.raises(
        ValueError,
        match="Report interview ID does not match.",
    ):
        generate_final_report(request, interview)


def test_final_report_request_duplicate_question_ids():
    request = create_request()

    questions = [
        vars(question).copy()
        for question in request.questions
    ]

    questions[9]["question_id"] = 9

    request_data = {
        "interview_id": request.interview_id,
        "resume_text": request.resume_text,
        "job_description": request.job_description,
        "questions": questions,
    }

    with pytest.raises(ValidationError) as exc_info:
        FinalReportRequest.model_validate(request_data)

    assert "Question IDs must be unique." in str(exc_info.value)


def test_final_report_request_duplicate_sequence_numbers():
    request = create_request()

    questions = [
        vars(question).copy()
        for question in request.questions
    ]

    questions[9]["sequence_number"] = 9

    request_data = {
        "interview_id": request.interview_id,
        "resume_text": request.resume_text,
        "job_description": request.job_description,
        "questions": questions,
    }

    with pytest.raises(ValidationError) as exc_info:
        FinalReportRequest.model_validate(request_data)

    assert "Sequence numbers must be unique." in str(exc_info.value)


def test_final_report_response_duplicate_dimensions():
    response_data = {
        "interview_id": 1001,
        "interview_summary": {
            "summary": "Good performance.",
            "strengths": ["Python knowledge"],
            "job_relevance": "Relevant to the job.",
        },
        "improvement_areas": [],
        "dimension_scores": [
            {
                "dimension": "technical_depth",
                "score": 4,
                "evidence": "Good technical knowledge.",
            },
            {
                "dimension": "communication",
                "score": 4,
                "evidence": "Clear explanations.",
            },
            {
                "dimension": "domain_experience",
                "score": 3,
                "evidence": "Some relevant experience.",
            },
            {
                "dimension": "technical_depth",
                "score": 4,
                "evidence": "Repeated dimension.",
            },
        ],
        "discrepancy_flags": [],
    }

    with pytest.raises(
        ValidationError,
        match="Each evaluation dimension must appear exactly once.",
    ):
        FinalReportResponse.model_validate(response_data)


def test_final_report_response_all_unique_dimensions():
    response_data = {
        "interview_id": 1001,
        "interview_summary": {
            "summary": "Good performance.",
            "strengths": ["Python knowledge"],
            "job_relevance": "Relevant to the job.",
        },
        "improvement_areas": [],
        "dimension_scores": [
            {
                "dimension": "technical_depth",
                "score": 4,
                "evidence": "Good technical knowledge.",
            },
            {
                "dimension": "communication",
                "score": 4,
                "evidence": "Clear explanations.",
            },
            {
                "dimension": "domain_experience",
                "score": 3,
                "evidence": "Some relevant experience.",
            },
            {
                "dimension": "problem_solving",
                "score": 4,
                "evidence": "Reasonable approach.",
            },
        ],
        "discrepancy_flags": [],
    }

    result = FinalReportResponse.model_validate(response_data)

    assert len(result.dimension_scores) == 4
    assert len({item.dimension for item in result.dimension_scores}) == 4


def test_generate_final_report_question_mismatch():
    request = create_request()
    interview = create_interview()

    interview["questions"] = GeneratedQuestions(
        questions=[
            {
                "id": i,
                "text": f"Original question {i}",
                "type": "main",
            }
            for i in range(1, 11)
        ]
    )

    with pytest.raises(
        ValueError,
        match="Question mismatch for question 1.",
    ):
        generate_final_report(request, interview)


def test_generate_final_report_question_match(monkeypatch):
    request = create_request()
    interview = create_interview()

    interview["questions"] = GeneratedQuestions(
        questions=[
            {
                "id": i,
                "text": f"Question {i}",
                "type": "main",
            }
            for i in range(1, 11)
        ]
    )

    expected_result = create_expected_result()

    monkeypatch.setattr(
        "app.final_report_generator.ask_llm_json",
        lambda *args, **kwargs: expected_result,
    )

    result = generate_final_report(request, interview)

    assert result.interview_id == request.interview_id
