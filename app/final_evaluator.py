
from app.llm import ask_llm_json
from app.final_evaluation_schemas import FinalInterviewEvaluation
from prompts.evaluate_final_interview import (
    EVALUATE_FINAL_INTERVIEW_PROMPT,
)

import json


def evaluate_final_interview(
    interview_data: dict,
) -> FinalInterviewEvaluation:

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

<interview_plan>
{json.dumps(
    interview_data["plan"],
    ensure_ascii=False,
)}
</interview_plan>

<interview_answers>
{json.dumps(
    interview_data["answers"],
    ensure_ascii=False,
)}
</interview_answers>

<matching_skills>
{json.dumps(
    interview_data["matching_skills"],
    ensure_ascii=False,
)}
</matching_skills>

<missing_skills>
{json.dumps(
    interview_data["missing_skills"],
    ensure_ascii=False,
)}
</missing_skills>
"""

    result = ask_llm_json(
        EVALUATE_FINAL_INTERVIEW_PROMPT,
        user_message,
    )

    return FinalInterviewEvaluation.model_validate(result)
