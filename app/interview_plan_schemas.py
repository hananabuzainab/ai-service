
from typing import Literal

from pydantic import Field

from app.schemas import BaseSchema


InterviewCategory = Literal[
    "behavioral",
    "technical",
]

InterviewDimension = Literal[
    "technical_depth",
    "communication",
    "domain_experience",
    "problem_solving",
]


class PlannedQuestion(BaseSchema):
    question_id: int = Field(ge=1, le=10)

    category: InterviewCategory

    question_type: str = Field(
        min_length=1,
        max_length=50,
    )

    skill: str | None = Field(
        default=None,
        max_length=100,
    )

    difficulty: Literal[
        "easy",
        "medium",
        "hard",
    ]

    primary_dimension: InterviewDimension

    secondary_dimensions: list[InterviewDimension] = Field(
        default_factory=list,
        max_length=3,
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


class GeneratedQuestion(BaseSchema):
    question: str = Field(min_length=5, max_length=2000)    
