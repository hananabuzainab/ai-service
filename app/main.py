
import logging

from fastapi import FastAPI, File, UploadFile, HTTPException

from app.llm import ask_llm_json
from app.pdf_utils import (
    extract_text_from_bytes,
    ResumeError,
    MAX_SIZE,
)
from prompts.extract_skills import (
    EXTRACT_RESUME_PROMPT,
    EXTRACT_JOB_PROMPT,
)
from app.skills_clean import (
    clean_resume_skills,
    clean_job_skills,
    limit_text,
)
from app.schemas import (
    ResumeResponse,
    JobRequest,
    JobResponse,
)
from app.roadmap import sort_skills, generate_roadmap
from app.roadmap_schemas import RoadmapRequest, RoadmapsResponse
from app.skill_rules import (
    refine_resume_skills,
    refine_job_skills,
)

from app.interview_schemas import (
    InterviewStartRequest,
    InterviewAnswerRequest,
)
from app.interview_planner import create_interview_plan
from app.question_generator import generate_interview_question
from app.interview_evaluator import evaluate_interview_answer
from app.follow_up_generator import generate_follow_up_question
from app.final_evaluator import evaluate_final_interview
from uuid import uuid4


# --------------------------------------------------
# Application configuration
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

app = FastAPI(title="Sparr AI Service")
# Temporary interview storage
interviews = {}


# --------------------------------------------------
# Error handling
# --------------------------------------------------

def error_detail(code, message):
    return {
        "error": {
            "code": code,
            "message": message,
        }
    }


# --------------------------------------------------
# Shared skill extraction
# --------------------------------------------------

def extract_skills_from_text(text, tag, prompt, cleaner):
    try:
        user_message = f"<{tag}>\n{text}\n</{tag}>"

        result = ask_llm_json(prompt, user_message)

        if not isinstance(result, dict):
            raise ValueError("AI response must be a JSON object")

        raw_skills = result.get("skills")

        if not isinstance(raw_skills, list):
            raise ValueError("AI response must contain a skills list")

        return cleaner(raw_skills)

    except Exception as error:

        logger.exception(
            "Skill extraction failed. Error type: %s",
            type(error).__name__,
        )

        raise HTTPException(
            status_code=502,
            detail=error_detail(
                "AI_FAILED",
                "Could not extract skills.",
            ),
        ) from error


# --------------------------------------------------
# 1. Health check
# --------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# --------------------------------------------------
# 2. Extract resume skills
# --------------------------------------------------

@app.post(
    "/v1/extract-resume",
    response_model=ResumeResponse,
)
def extract_resume(file: UploadFile = File(...)):

    # Read only MAX_SIZE + 1 bytes.
    # The extra byte tells us whether the file exceeds the limit.
    data = file.file.read(MAX_SIZE + 1)

    try:
        text = extract_text_from_bytes(
            data,
            file.filename,
        )

    except ResumeError as error:
        raise HTTPException(
            status_code=422,
            detail=error_detail(
                error.code,
                error.message,
            ),
        ) from error

    skills = extract_skills_from_text(
        text,
        "resume",
        EXTRACT_RESUME_PROMPT,
        lambda raw: clean_resume_skills(
            refine_resume_skills(raw)
        ),
    )

    return ResumeResponse(
        extracted_text=limit_text(text),
        skills=skills,
    )


# --------------------------------------------------
# 3. Extract job description skills
# --------------------------------------------------

@app.post(
    "/v1/extract-job",
    response_model=JobResponse,
)
def extract_job(req: JobRequest):

    skills = extract_skills_from_text(
        req.text,
        "job",
        EXTRACT_JOB_PROMPT,
        lambda raw: clean_job_skills(
            refine_job_skills(raw)
        ),
    )

    return JobResponse(
        skills=skills,
    )


# --------------------------------------------------
# 4. Generate learning roadmaps
# --------------------------------------------------

MAX_ROADMAPS = 5


@app.post(
    "/v1/generate-roadmap",
    response_model=RoadmapsResponse,
)
def generate_roadmaps(req: RoadmapRequest):

    if not req.missing_skills:
        return RoadmapsResponse(
            roadmaps=[],
        )

    skills = sort_skills(
        [skill.model_dump() for skill in req.missing_skills]
    )[:MAX_ROADMAPS]

    known = [
        skill.name
        for skill in req.matching_skills
    ]

    roadmaps = []

    for priority, skill in enumerate(skills, start=1):

        try:
            roadmap = generate_roadmap(
                skill,
                priority,
                req.job_title,
                known,
            )

            roadmaps.append(roadmap)

        except Exception as error:

            logger.exception(
                "Roadmap generation failed. Error type: %s",
                type(error).__name__,
            )

            raise HTTPException(
                status_code=502,
                detail=error_detail(
                    "AI_FAILED",
                    "Could not generate the roadmap.",
                ),
            ) from error

    return RoadmapsResponse(
        roadmaps=roadmaps,
    )


# --------------------------------------------------
# 5. Start interview
# --------------------------------------------------

@app.post("/v1/interview/start")
def start_interview(req: InterviewStartRequest):

    interview_id = str(uuid4())

    # 1. Store interview data
    interviews[interview_id] = req.model_dump()
    interviews[interview_id]["answers"] = []
    interviews[interview_id]["follow_up_count"] = 0
    interviews[interview_id]["processed_requests"] = {}

    # 2. Generate interview plan
    plan = create_interview_plan(interviews[interview_id])

    # 3. Save the plan
    interviews[interview_id]["plan"] = plan.model_dump()
    print(interviews[interview_id]["plan"]["questions"])
    # 4. Get the first planned question
    first_planned_question = interviews[interview_id]["plan"]["questions"][0]

    # 5. Generate the actual question
    question = generate_interview_question(
        interviews[interview_id],
        first_planned_question,
    )

    # 6. Save the first question
    interviews[interview_id]["current_question"] = {
    "question_id": first_planned_question["question_id"],
    "question": question.question,
    "is_follow_up": False,
    "follow_up_used": False,
    }

    return {
        "status": "success",
        "interview_id": interview_id,
        "question_id": first_planned_question["question_id"],
        "question": question.question,
        "message": "Interview started successfully.",
    }





# --------------------------------------------------
# 6. Submit interview answer
# --------------------------------------------------

@app.post("/v1/interview/answer")
def submit_interview_answer(req: InterviewAnswerRequest):

    # 1. Find the interview
    interview = interviews.get(req.interview_id)

    if interview is None:
        raise HTTPException(
            status_code=404,
            detail=error_detail(
                "INTERVIEW_NOT_FOUND",
                "Interview not found.",
            ),
        )

    # 2. Check if this request was already processed
    processed_request = interview["processed_requests"].get(req.request_id)
    print("REQUEST ID:", req.request_id)
    print("SAVED REQUEST IDS:", list(interview["processed_requests"].keys()))

    if processed_request is not None:

        # Make sure the same request_id is not used for different data
        if (
            processed_request["question_id"] != req.question_id
            or processed_request["answer"] != req.answer
        ):
            raise HTTPException(
                status_code=409,
                detail=error_detail(
                    "REQUEST_ID_CONFLICT",
                    "This request ID was already used for a different answer.",
                ),
            )

        # Return the previously saved response
        return processed_request["response"]

    # 3. Get the current question
    current_question = interview.get("current_question")

    if current_question is None:
        raise HTTPException(
            status_code=400,
            detail=error_detail(
                "NO_CURRENT_QUESTION",
                "There is no active question.",
            ),
        )

    # 4. Verify that the answer belongs to the current question
    if req.question_id != current_question["question_id"]:
        raise HTTPException(
            status_code=409,
            detail=error_detail(
                "QUESTION_ID_MISMATCH",
                "This answer does not belong to the current question.",
            ),
        )

    # 5. Save the successful response for duplicate request handling
    def save_processed_request(response):
        interview["processed_requests"][req.request_id] = {
            "question_id": req.question_id,
            "answer": req.answer,
            "response": response,
        }

        return response

    # 6. Find the planned question
    question_id = current_question["question_id"]

    planned_question = next(
        (
            question
            for question in interview["plan"]["questions"]
            if question["question_id"] == question_id
        ),
        None,
    )

    if planned_question is None:
        raise HTTPException(
            status_code=500,
            detail=error_detail(
                "QUESTION_NOT_FOUND",
                "Could not find the question plan.",
            ),
        )

    # 7. Evaluate the candidate's answer
    try:
        evaluation = evaluate_interview_answer(
            interview,
            planned_question,
            current_question["question"],
            req.answer,
        )

    except Exception as error:
        logger.exception(
            "Interview answer evaluation failed. Error type: %s",
            type(error).__name__,
        )

        raise HTTPException(
            status_code=502,
            detail=error_detail(
                "AI_FAILED",
                "Could not evaluate the interview answer.",
            ),
        ) from error

    # 8. Prepare the answer record
    answer_record = {
        "question_id": question_id,
        "question": current_question["question"],
        "answer": req.answer,
        "is_follow_up": current_question["is_follow_up"],
        "evaluation": evaluation.model_dump(),
    }

    # 9. Check whether a follow-up question is needed
    if (
        evaluation.needs_follow_up
        and not current_question["follow_up_used"]
        and interview["follow_up_count"] < 3
    ):

        try:
            follow_up = generate_follow_up_question(
                current_question["question"],
                req.answer,
                evaluation.follow_up_reason,
            )

        except Exception as error:
            logger.exception(
                "Follow-up generation failed. Error type: %s",
                type(error).__name__,
            )

            raise HTTPException(
                status_code=502,
                detail=error_detail(
                    "AI_FAILED",
                    "Could not generate a follow-up question.",
                ),
            ) from error

        # 10. Save the answer after successful follow-up generation
        interview["answers"].append(answer_record)

        # 11. Update follow-up counter
        interview["follow_up_count"] += 1

        # 12. Save the follow-up as the current question
        interview["current_question"] = {
            "question_id": question_id,
            "question": follow_up.question,
            "is_follow_up": True,
            "follow_up_used": True,
        }

        response = {
            "status": "success",
            "question_id": question_id,
            "is_follow_up": True,
            "question": follow_up.question,
            "evaluation": evaluation.model_dump(),
        }

        return save_processed_request(response)

    # 13. Move to the next main question
    next_question_id = question_id + 1

    next_planned_question = next(
        (
            question
            for question in interview["plan"]["questions"]
            if question["question_id"] == next_question_id
        ),
        None,
    )

    # 14. Check whether the interview is completed
    if next_planned_question is None:

        # The final evaluator needs the latest answer in the answers list
        interview["answers"].append(answer_record)

        try:
            final_evaluation = evaluate_final_interview(interview)

        except Exception as error:
            # Roll back the answer if final evaluation fails
            interview["answers"].pop()

            logger.exception(
                "Final interview evaluation failed. Error type: %s",
                type(error).__name__,
            )

            raise HTTPException(
                status_code=502,
                detail=error_detail(
                    "AI_FAILED",
                    "Could not generate the final interview evaluation.",
                ),
            ) from error

        # 15. Save the final evaluation
        interview["final_evaluation"] = final_evaluation.model_dump()
        interview["current_question"] = None
        interview["status"] = "completed"

        response = {
            "status": "success",
            "question_id": question_id,
            "is_follow_up": False,
            "interview_completed": True,
            "evaluation": evaluation.model_dump(),
            "final_evaluation": final_evaluation.model_dump(),
            "message": "Interview completed successfully.",
        }

        return save_processed_request(response)

    # 16. Generate the next question
    try:
        next_question = generate_interview_question(
            interview,
            next_planned_question,
        )

    except Exception as error:
        logger.exception(
            "Next question generation failed. Error type: %s",
            type(error).__name__,
        )

        raise HTTPException(
            status_code=502,
            detail=error_detail(
                "AI_FAILED",
                "Could not generate the next interview question.",
            ),
        ) from error

    # 17. Save the answer after successful next-question generation
    interview["answers"].append(answer_record)

    # 18. Save the next question as current
    interview["current_question"] = {
        "question_id": next_question_id,
        "question": next_question.question,
        "is_follow_up": False,
        "follow_up_used": False,
    }

    response = {
        "status": "success",
        "question_id": question_id,
        "next_question_id": next_question_id,
        "is_follow_up": False,
        "interview_completed": False,
        "question": next_question.question,
        "evaluation": evaluation.model_dump(),
    }

    return save_processed_request(response)
