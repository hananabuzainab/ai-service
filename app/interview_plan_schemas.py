from typing import Literal

from pydantic import Field

from app.schemas import BaseSchema


EvaluationDimension = Literal[
    "technical_depth",
    "communication",
    "domain_experience",
    "problem_solving",
]


class PlannedQuestion(BaseSchema):
    id: int = Field(ge=1, le=10)

    category: Literal["behavioral", "technical"]

    skill: str | None = None

    difficulty: Literal["easy", "medium", "hard"]

    primary_dimension: EvaluationDimension

    secondary_dimensions: list[EvaluationDimension] = Field(
        default_factory=list
    )

    evaluation_criteria: list[str] = Field(
        min_length=2,
        max_length=5,
    )


class InterviewPlan(BaseSchema):
    questions: list[PlannedQuestion] = Field(
        min_length=10,
        max_length=10,
    )