
import pytest

from pydantic import ValidationError

from app.schemas import (
    ResumeSkill,
    JobSkill,
    ResumeResponse,
    JobRequest,
    JobResponse,
)


def test_valid_resume_skill():
    skill = ResumeSkill(
        name="Python",
        category="languages",
        confidence_score=0.95,
    )

    assert skill.name == "Python"
    assert skill.confidence_score == 0.95


def test_resume_skill_optional_confidence():
    skill = ResumeSkill(
        name="Python",
        category="languages",
    )

    assert skill.confidence_score is None


def test_empty_skill_name_rejected():
    with pytest.raises(ValidationError):
        ResumeSkill(
            name="",
            category="languages",
        )


def test_invalid_category_rejected():
    with pytest.raises(ValidationError):
        ResumeSkill(
            name="Python",
            category="programming",
        )


def test_invalid_confidence_score_rejected():
    with pytest.raises(ValidationError):
        ResumeSkill(
            name="Python",
            category="languages",
            confidence_score=1.5,
        )


def test_valid_job_skill():
    skill = JobSkill(
        name="Django",
        category="frameworks",
        importance=0.9,
    )

    assert skill.importance == 0.9


def test_invalid_job_importance_rejected():
    with pytest.raises(ValidationError):
        JobSkill(
            name="Django",
            category="frameworks",
            importance=-0.2,
        )


def test_job_request_valid():
    request = JobRequest(
        text="We are looking for a Python backend developer."
    )

    assert "Python" in request.text


def test_short_job_description_rejected():
    with pytest.raises(ValidationError):
        JobRequest(text="Python")


def test_long_job_description_rejected():
    with pytest.raises(ValidationError):
        JobRequest(text="A" * 65536)


def test_extra_fields_rejected():
    with pytest.raises(ValidationError):
        ResumeSkill(
            name="Python",
            category="languages",
            confidence_score=0.9,
            unexpected_field="value",
        )


def test_resume_response():
    response = ResumeResponse(
        extracted_text="Candidate has Python experience.",
        skills=[
            {
                "name": "Python",
                "category": "languages",
                "confidence_score": 0.9,
            }
        ],
    )

    assert len(response.skills) == 1
    assert response.skills[0].name == "Python"


def test_job_response():
    response = JobResponse(
        skills=[
            {
                "name": "Django",
                "category": "frameworks",
                "importance": 0.9,
            }
        ],
    )

    assert response.skills[0].importance == 0.9
