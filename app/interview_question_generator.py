import json

from app.llm import ask_llm_json
from app.interview_schemas import InterviewStartRequest
from app.interview_plan_schemas import InterviewPlan
from app.interview_generation_schemas import GeneratedQuestions
from prompts.generate_interview_questions import (
    GENERATE_INTERVIEW_QUESTIONS_PROMPT,
)


def generate_interview_questions(
    req: InterviewStartRequest,
    plan: InterviewPlan,
):
    user_message = f"""
<JOB_TITLE>
{req.job_title}
</JOB_TITLE>

<JOB_DESCRIPTION>
{req.job_description}
</JOB_DESCRIPTION>

<RESUME>
{req.resume}
</RESUME>

<INTERVIEW_PLAN>
{json.dumps(
    plan.model_dump(),
    ensure_ascii=False,
)}
</INTERVIEW_PLAN>
"""

    result = ask_llm_json(
        GENERATE_INTERVIEW_QUESTIONS_PROMPT,
        user_message,
        response_schema=GeneratedQuestions,
    )

    generated = GeneratedQuestions.model_validate(result)

    # Ensure generated question IDs match the interview plan.
    planned_ids = [question.id for question in plan.questions]
    generated_ids = [question.id for question in generated.questions]

    if generated_ids != planned_ids:
        raise ValueError(
            "Generated question IDs must match the interview plan."
        )

    # Ensure all generated questions are main questions.
    if any(question.type != "main" for question in generated.questions):
        raise ValueError(
            "All generated questions must have type 'main'."
        )

    return generated