
from typing import Literal

from pydantic import Field

from app.schemas import BaseSchema


# --------------------------------------------------
# 1. Skill Assessment
# --------------------------------------------------

class SkillAssessment(BaseSchema):
    skill_name: str = Field(
        min_length=1,
        max_length=100,
    )

    score: float | None = Field(
        default=None,
        ge=0,
        le=5,
    )

    evidence: list[str] = Field(
        default_factory=list,
    )

    question_ids: list[int] = Field(
        default_factory=list,
    )


# --------------------------------------------------
# 2. Dimension Assessment
# --------------------------------------------------

InterviewDimension = Literal[
    "technical_depth",
    "communication",
    "domain_experience",
    "problem_solving",
]


class DimensionAssessment(BaseSchema):
    dimension: InterviewDimension

    score: float | None = Field(
        default=None,
        ge=0,
        le=5,
    )

    evidence: list[str] = Field(
        default_factory=list,
    )

    question_ids: list[int] = Field(
        default_factory=list,
    )


# --------------------------------------------------
# 3. Resume Discrepancy
# --------------------------------------------------

class ResumeDiscrepancy(BaseSchema):
    resume_claim: str

    interview_evidence: str

    question_ids: list[int] = Field(
        default_factory=list,
    )

    explanation: str


# --------------------------------------------------
# 4. Final Interview Evaluation
# --------------------------------------------------

class FinalInterviewEvaluation(BaseSchema):
    skill_assessments: list[SkillAssessment] = Field(
        default_factory=list,
    )

    dimension_assessments: list[DimensionAssessment] = Field(
        min_length=4,
        max_length=4,
    )

    strengths: list[str] = Field(
        default_factory=list,
    )

    improvements: list[str] = Field(
        default_factory=list,
    )

    discrepancies: list[ResumeDiscrepancy] = Field(
        default_factory=list,
    )
