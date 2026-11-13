
import json

from app.llm import ask_llm_json
from app.final_report_schemas import (
    FinalReportRequest,
    FinalReportResponse,
)
from prompts.generate_final_report import (
    GENERATE_FINAL_REPORT_PROMPT,
)


def generate_final_report(
    req: FinalReportRequest,
    interview: dict,
):
    # Step 1: Retrieve the stored interview evaluations.
    evaluations = interview.get("evaluations", {})

    # Step 2: Verify that all 10 questions have evaluations.
    if len(evaluations) != 10:
        raise ValueError(
            "All 10 interview questions must be evaluated."
        )

    report_data = []

    # Step 3: Match each backend question with its internal evaluation.
    for question in req.questions:

        question_id = question.question_id

        stored_data = evaluations.get(question_id)

        if stored_data is None:
            raise ValueError(
                f"Evaluation not found for question {question_id}."
            )

        evaluation = stored_data["evaluation"]

        # Verify that the backend and AI Service have the same answer.
        if stored_data["answer"] != question.answer:
            raise ValueError(
                f"Answer mismatch for question {question_id}."
            )

        # Verify that the public evaluation matches the stored evaluation.
        if (
            evaluation.score != question.score
            or evaluation.better_answer != question.better_answer
        ):
            raise ValueError(
                f"Evaluation mismatch for question {question_id}."
            )

        # Retrieve the original planned question.
        planned_question = next(
            (
                item
                for item in interview["plan"].questions
                if item.id == question_id
            ),
            None,
        )

        if planned_question is None:
            raise ValueError(
                f"Question {question_id} not found in interview plan."
            )

                # Retrieve the original generated question.
        stored_question = next(
            (
                item
                for item in interview["questions"].questions
                if item.id == question_id
            ),
            None,
        )

        if stored_question is None:
            raise ValueError(
                f"Question {question_id} not found in interview."
            )

        # Verify that the backend sent the original question.
        if stored_question.text != question.question:
            raise ValueError(
                f"Question mismatch for question {question_id}."
            )

        report_data.append(
            {
                "question_id": question_id,
                "sequence_number": question.sequence_number,
                "question": question.question,
                "answer": question.answer,
                "score": question.score,
                "better_answer": question.better_answer,
                "category": planned_question.category,
                "skill": planned_question.skill,
                "difficulty": planned_question.difficulty,
                "primary_dimension": planned_question.primary_dimension,
                "secondary_dimensions": planned_question.secondary_dimensions,
                "evaluation_criteria": planned_question.evaluation_criteria,
                "criteria_results": [
                    result.model_dump()
                    for result in evaluation.criteria_results
                ],
            }
        )

    # Step 4: Prepare all interview data for Gemini.
    user_message = f"""
<INTERVIEW_ID>
{req.interview_id}
</INTERVIEW_ID>

<RESUME>
{req.resume_text}
</RESUME>

<JOB_DESCRIPTION>
{req.job_description}
</JOB_DESCRIPTION>

<INTERVIEW_QUESTIONS_AND_EVALUATIONS>
{json.dumps(report_data, ensure_ascii=False)}
</INTERVIEW_QUESTIONS_AND_EVALUATIONS>
"""

    # Step 5: Generate the final report.
    result = ask_llm_json(
        GENERATE_FINAL_REPORT_PROMPT,
        user_message,
        response_schema=FinalReportResponse,
    )

    report = FinalReportResponse.model_validate(result)

    # Step 6: Verify the returned interview ID.
    if report.interview_id != req.interview_id:
        raise ValueError(
            "Report interview ID does not match."
        )

    return report
