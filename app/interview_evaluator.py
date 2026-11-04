from app.llm import ask_llm_json
from app.interview_schemas import InterviewEvaluation
from prompts.evaluate_interview_answer import (
    EVALUATE_INTERVIEW_ANSWER_PROMPT,
)


def evaluate_interview_answer(
    interview_data: dict,
    planned_question: dict,
    question: str,
    answer: str,
) -> InterviewEvaluation:

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

<interview_question>
{question}
</interview_question>

<evaluation_criteria>
{planned_question["evaluation_criteria"]}
</evaluation_criteria>

<candidate_answer>
{answer}
</candidate_answer>
"""

    result = ask_llm_json(
        EVALUATE_INTERVIEW_ANSWER_PROMPT,
        user_message,
    )

    return InterviewEvaluation.model_validate(result)