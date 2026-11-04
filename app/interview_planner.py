import json

from app.llm import ask_llm_json
from app.interview_plan_schemas import InterviewPlan
from prompts.plan_interview import PLAN_INTERVIEW_PROMPT


def create_interview_plan(interview_data: dict) -> InterviewPlan:
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

<matching_skills>
{json.dumps(interview_data["matching_skills"], ensure_ascii=False)}
</matching_skills>

<missing_skills>
{json.dumps(interview_data["missing_skills"], ensure_ascii=False)}
</missing_skills>
"""

    result = ask_llm_json(
    PLAN_INTERVIEW_PROMPT,
    user_message,
    )

    return InterviewPlan.model_validate(result)