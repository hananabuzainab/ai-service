
from typing import Literal

from app.schemas import BaseSchema

from pydantic import Field, model_validator

# --------------------------------------------------
# Questions received from backend
# --------------------------------------------------

class FinalReportQuestion(BaseSchema):
    question_id: int = Field(
        ge=1,
        le=10,
    )

    sequence_number: int = Field(
        ge=1,
        le=10,
    )

    question: str = Field(
        min_length=1,
    )

    answer: str = Field(
        min_length=1,
    )

    score: float = Field(
        ge=0,
        le=10,
    )

    better_answer: str


# --------------------------------------------------
# Final report request
# --------------------------------------------------

class FinalReportRequest(BaseSchema):
    interview_id: int = Field(ge=1)

    resume_text: str = Field(
        min_length=50,
    )

    job_description: str = Field(
        min_length=20,
    )

    questions: list[FinalReportQuestion] = Field(
        min_length=10,
        max_length=10,
    )
    @model_validator(mode="after")
    def validate_questions(self):

        question_ids = [
            question.question_id
            for question in self.questions
        ]

        sequence_numbers = [
            question.sequence_number
            for question in self.questions
        ]

        if len(set(question_ids)) != 10:
            raise ValueError(
                "Question IDs must be unique."
            )

        if len(set(sequence_numbers)) != 10:
            raise ValueError(
                "Sequence numbers must be unique."
            )

        return self


# --------------------------------------------------
# Interview summary
# --------------------------------------------------

class InterviewSummary(BaseSchema):
    summary: str

    strengths: list[str]

    job_relevance: str


# --------------------------------------------------
# Improvement areas
# --------------------------------------------------

class ImprovementArea(BaseSchema):
    area: str

    recommendation: str


# --------------------------------------------------
# Dimension scores
# --------------------------------------------------

EvaluationDimension = Literal[
    "technical_depth",
    "communication",
    "domain_experience",
    "problem_solving",
]


class DimensionScore(BaseSchema):
    dimension: EvaluationDimension

    score: float = Field(
        ge=0,
        le=5,
    )

    evidence: str


# --------------------------------------------------
# Discrepancy flags
# --------------------------------------------------

class DiscrepancyFlag(BaseSchema):
    cv_claim: str

    interview_claim: str


# --------------------------------------------------
# Final report response
# --------------------------------------------------

class FinalReportResponse(BaseSchema):
    interview_id: int

    interview_summary: InterviewSummary

    improvement_areas: list[ImprovementArea]

    dimension_scores: list[DimensionScore] = Field(
        min_length=4,
        max_length=4,
    )

    discrepancy_flags: list[DiscrepancyFlag]

    @model_validator(mode="after")
    def validate_dimension_scores(self):

        dimensions = [
            item.dimension
            for item in self.dimension_scores
        ]

        if len(set(dimensions)) != 4:
            raise ValueError(
                "Each evaluation dimension must appear exactly once."
            )

        return self
