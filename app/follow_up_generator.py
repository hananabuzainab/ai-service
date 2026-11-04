from app.llm import ask_llm_json
from app.interview_plan_schemas import GeneratedQuestion
from prompts.generate_follow_up import (
    GENERATE_FOLLOW_UP_PROMPT,
)


def generate_follow_up_question(
    interview_question: str,
    candidate_answer: str,
    follow_up_reason: str,
) -> GeneratedQuestion:

    user_message = f"""
<original_question>
{interview_question}
</original_question>

<candidate_answer>
{candidate_answer}
</candidate_answer>

<follow_up_reason>
{follow_up_reason}
</follow_up_reason>
"""

    result = ask_llm_json(
        GENERATE_FOLLOW_UP_PROMPT,
        user_message,
    )

    return GeneratedQuestion.model_validate(result)