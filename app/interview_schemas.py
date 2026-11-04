
from pydantic import Field

from app.schemas import BaseSchema

from typing import Literal

class InterviewSkill(BaseSchema):
    id: int | None = None

    name: str = Field(
        min_length=1,
        max_length=45,
    )

    category: str = "other"

    importance: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    candidate_confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )


class InterviewStartRequest(BaseSchema):
    job_title: str = Field(
        min_length=1,
        max_length=200,
    )

    job_description: str = Field(
        min_length=20,
    )

    resume_text: str = Field(
        min_length=1,
    )

    matching_skills: list[InterviewSkill] = Field(
        default_factory=list,
        max_length=100,
    )

    missing_skills: list[InterviewSkill] = Field(
        default_factory=list,
        max_length=100,
    )

class InterviewAnswerRequest(BaseSchema):
    interview_id: str = Field(min_length=1)
    question_id: int = Field(ge=1)
    request_id: str = Field(min_length=1)
    answer: str = Field(min_length=1, max_length=10000) 


class CriterionResult(BaseSchema):
    criterion: str
    status: Literal["met", "partially_met", "not_met", "insufficient_evidence"]
    evidence: str | None = None


class InterviewEvaluation(BaseSchema):
    criteria_results: list[CriterionResult]
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    needs_follow_up: bool
    follow_up_reason: str | None = None