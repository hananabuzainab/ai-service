
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# Allowed skill categories across the application.
SkillCategory = Literal[
    "languages",
    "frameworks",
    "databases",
    "cloud_devops",
    "ml_data",
    "tools",
    "other",
]


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class ResumeSkill(BaseSchema):
    name: str = Field(
        min_length=1,
        max_length=45,
    )

    category: SkillCategory

    confidence_score: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )


class JobSkill(BaseSchema):
    name: str = Field(
        min_length=1,
        max_length=45,
    )

    category: SkillCategory

    importance: float = Field(
        ge=0,
        le=1,
    )


class ResumeResponse(BaseSchema):
    extracted_text: str

    skills: list[ResumeSkill] = Field(
        max_length=500,
    )


class JobRequest(BaseSchema):
    text: str = Field(
        min_length=20,
        max_length=65535,
    )


class JobResponse(BaseSchema):
    skills: list[JobSkill] = Field(
        max_length=500,
    )
