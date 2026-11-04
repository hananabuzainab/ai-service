from app.llm import ask_llm_json
from app.interview_plan_schemas import GeneratedQuestion
from prompts.generate_interview_question import (
    GENERATE_INTERVIEW_QUESTION_PROMPT,
)


def generate_interview_question(
    interview_data: dict,
    planned_question: dict,
) -> GeneratedQuestion:

    user_message = f"""
<job_title>
{interview_data["job_title"]}
</job_title>

<job_description>
{interview_data["job_description"]}
</job_description>

<resume>
{interview_data["resume_text"]}
</resume>

<question_plan>
{planned_question}
</question_plan>
"""

    result = ask_llm_json(
        GENERATE_INTERVIEW_QUESTION_PROMPT,
        user_message,
    )

    return GeneratedQuestion.model_validate(result)