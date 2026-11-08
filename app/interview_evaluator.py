import json

from app.llm import ask_llm_json
from app.interview_schemas import (
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewInternalEvaluation,
)
from prompts.evaluate_interview_answer import (
    EVALUATE_INTERVIEW_ANSWER_PROMPT,
)


def evaluate_interview_answer(
    req: InterviewAnswerRequest,
    interview: dict,
):
    question_id = int(req.id)

    # Find the planned question.
    planned_question = next(
        (
            question
            for question in interview["plan"].questions
            if question.id == question_id
        ),
        None,
    )

    if planned_question is None:
        raise ValueError("Question not found in interview plan.")

    # Find the actual generated question.
    generated_question = next(
        (
            question
            for question in interview["questions"].questions
            if question.id == question_id
        ),
        None,
    )

    if generated_question is None:
        raise ValueError("Generated question not found.")

    # Retrieve the original interview request.
    original_request = interview["request"]

    user_message = f"""
<QUESTION_ID>
{req.id}
</QUESTION_ID>

<JOB_TITLE>
{original_request.job_title}
</JOB_TITLE>

<JOB_DESCRIPTION>
{original_request.job_description}
</JOB_DESCRIPTION>


<RESUME>
{original_request.resume}
</RESUME>

<QUESTION>
{generated_question.text}
</QUESTION>

<CATEGORY>
{planned_question.category}
</CATEGORY>

<SKILL>
{planned_question.skill or "Not applicable"}
</SKILL>

<DIFFICULTY>
{planned_question.difficulty}
</DIFFICULTY>

<EVALUATION_DIMENSIONS>
{json.dumps(
    {
        "primary": planned_question.primary_dimension,
        "secondary": planned_question.secondary_dimensions,
    },
    ensure_ascii=False,
)}
</EVALUATION_DIMENSIONS>

<EVALUATION_CRITERIA>
{json.dumps(
    planned_question.evaluation_criteria,
    ensure_ascii=False,
)}
</EVALUATION_CRITERIA>

<CANDIDATE_ANSWER>
{req.text}
</CANDIDATE_ANSWER>
"""

    # Step 1: Get the complete evaluation from Gemini.
    result = ask_llm_json(
        EVALUATE_INTERVIEW_ANSWER_PROMPT,
        user_message,
        response_schema=InterviewInternalEvaluation,
    )

    evaluation = InterviewInternalEvaluation.model_validate(result)

    # Step 2: Verify the returned question ID.
    if evaluation.id != req.id:
        raise ValueError("Evaluation question ID does not match.")

    # Step 3: Save the answer and full evaluation internally.
    interview.setdefault("evaluations", {})[req.id] = {
        "answer": req.text,
        "evaluation": evaluation,
    }

    # Step 4: Return only the public response to the backend.
    return InterviewAnswerResponse(
        id=evaluation.id,
        score=evaluation.score,
        better_answer=evaluation.better_answer,
    )