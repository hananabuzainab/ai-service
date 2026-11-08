import json

from app.llm import ask_llm_json
from app.interview_schemas import InterviewStartRequest
from app.interview_plan_schemas import InterviewPlan
from prompts.plan_interview import PLAN_INTERVIEW_PROMPT


# --------------------------------------------------
# Generate interview plan
# --------------------------------------------------

def generate_interview_plan(req: InterviewStartRequest):

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

<MATCHING_SKILLS>
{json.dumps(
    [skill.model_dump() for skill in req.matching_skills],
    ensure_ascii=False,
)}
</MATCHING_SKILLS>

<MISSING_SKILLS>
{json.dumps(
    [skill.model_dump() for skill in req.missing_skills],
    ensure_ascii=False,
)}
</MISSING_SKILLS>
"""

    result = ask_llm_json(
        PLAN_INTERVIEW_PROMPT,
        user_message,
        response_schema=InterviewPlan,
    )

    plan = InterviewPlan.model_validate(result)

    # Validate question distribution.
    behavioral_count = sum(
        question.category == "behavioral"
        for question in plan.questions
    )

    technical_count = sum(
        question.category == "technical"
        for question in plan.questions
    )

    if behavioral_count != 4 or technical_count != 6:
        raise ValueError(
            "Interview plan must contain "
            "4 behavioral and 6 technical questions."
        )

    # Validate sequential question IDs.
    question_ids = [
        question.id
        for question in plan.questions
    ]

    if question_ids != list(range(1, 11)):
        raise ValueError(
            "Question IDs must be sequential from 1 to 10."
        )

    return plan