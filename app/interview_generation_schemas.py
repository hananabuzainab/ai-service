from typing import Literal

from pydantic import Field

from app.schemas import BaseSchema


class GeneratedQuestion(BaseSchema):
    id: int = Field(ge=1, le=10)
    text: str = Field(min_length=10)
    type: Literal["main", "follow_up"] = "main"


class GeneratedQuestions(BaseSchema):
    questions: list[GeneratedQuestion] = Field(
        min_length=10,
        max_length=10,
    )