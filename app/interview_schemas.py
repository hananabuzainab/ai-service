from typing import Literal

from pydantic import Field

from app.schemas import BaseSchema, SkillCategory


# --------------------------------------------------
# Skills received from backend
# --------------------------------------------------

class InterviewMatchingSkill(BaseSchema):
    id: int

    name: str = Field(
        min_length=1,
        max_length=45,
    )

    category: SkillCategory

    importance: float = Field(
        ge=0,
        le=1,
    )

    candidate_confidence: float = Field(
        ge=0,
        le=1,
    )


class InterviewMissingSkill(BaseSchema):
    id: int

    name: str = Field(
        min_length=1,
        max_length=45,
    )

    category: SkillCategory

    importance: float = Field(
        ge=0,
        le=1,
    )


# --------------------------------------------------
# Interview start request
# --------------------------------------------------

class InterviewAnalysisData(BaseSchema):
    job_title: str = Field(
        min_length=1,
    )

    matching_skills: list[InterviewMatchingSkill]

    missing_skills: list[InterviewMissingSkill]


class InterviewStartRequest(BaseSchema):
    interview_id: int = Field(ge=1)
    resume: str = Field(min_length=50)
    job_description: str = Field(min_length=20)
    job_title: str = Field(min_length=1)
    missing_skills: list[InterviewMissingSkill]
    matching_skills: list[InterviewMatchingSkill]
# --------------------------------------------------
# Interview questions
# --------------------------------------------------

class InterviewQuestion(BaseSchema):
    id: int

    text: str = Field(
        min_length=1,
    )

    type: Literal[
        "main",
        "follow_up",
    ] = "main"


class InterviewStartResponse(BaseSchema):
    questions: list[InterviewQuestion] = Field(
        min_length=10,
        max_length=10,
    )


# --------------------------------------------------
# Interview answer request
# --------------------------------------------------

class InterviewAnswerRequest(BaseSchema):
    interview_id: int = Field(ge=1)

    id: int = Field(ge=1)

    text: str = Field(
        min_length=1,
    )


# --------------------------------------------------
# Interview answer evaluation response
# --------------------------------------------------

class InterviewAnswerResponse(BaseSchema):
    id: int
    score: float = Field(ge=0, le=10)
    better_answer: str


class CriterionResult(BaseSchema):
    criterion: str
    status: Literal[
        "met",
        "partially_met",
        "not_met",
        "insufficient_evidence",
    ]
    evidence: str | None = None


class InterviewInternalEvaluation(BaseSchema):
    id: int
    score: float = Field(ge=0, le=10)
    criteria_results: list[CriterionResult]
    better_answer: str    

