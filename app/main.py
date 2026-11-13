
import logging

from fastapi import FastAPI, File, UploadFile, HTTPException

from app.llm import (
    ask_llm_json,
    build_resume_skills_schema,
    build_job_skills_schema,
)
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
    InterviewStartResponse,
    InterviewAnswerRequest,
    InterviewAnswerResponse,
)
from app.interview_planner import generate_interview_plan
from app.interview_question_generator import (
    generate_interview_questions,
)
from app.interview_evaluator import evaluate_interview_answer
from app.final_report_schemas import (
    FinalReportRequest,
    FinalReportResponse,
)
from app.final_report_generator import generate_final_report


# --------------------------------------------------
# Application configuration
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

app = FastAPI(title="Sparr AI Service")


# --------------------------------------------------
# Interview storage
# --------------------------------------------------

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

def extract_skills_from_text(
    text,
    tag,
    prompt,
    cleaner,
    response_schema,
):
    try:
        user_message = f"<{tag}>\n{text}\n</{tag}>"

        result = ask_llm_json(
            prompt,
            user_message,
            response_schema=response_schema,
        )

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
        build_resume_skills_schema(),
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
        build_job_skills_schema(),
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
        return RoadmapsResponse(roadmaps=[])

    skills = sort_skills(
        [skill.model_dump() for skill in req.missing_skills]
    )

    known = [skill.name for skill in req.matching_skills]
    roadmaps = []

    for index, skill in enumerate(skills):

        if len(roadmaps) >= MAX_ROADMAPS:
            break

        priority = index + 1

        other_missing = [
            other["name"]
            for other in skills
            if other is not skill
        ]

        try:
            roadmap = generate_roadmap(
                skill,
                priority,
                req.job_title,
                known,
                other_missing,
            )

            roadmaps.append(roadmap)

        except Exception as error:
            logger.exception(
                "Roadmap generation failed for skill '%s'. Error type: %s",
                skill["name"],
                type(error).__name__,
            )
            continue

    if not roadmaps:
        raise HTTPException(
            status_code=502,
            detail=error_detail(
                "AI_FAILED",
                "Could not generate the roadmap.",
            ),
        )

    return RoadmapsResponse(roadmaps=roadmaps)


# --------------------------------------------------
# 5. Start interview
# --------------------------------------------------

@app.post(
    "/v1/interview/start",
    response_model=InterviewStartResponse,
)
def start_interview(req: InterviewStartRequest):

    try:
        # Step 1: Generate the interview plan.
        plan = generate_interview_plan(req)

        # Step 2: Generate the interview questions.
        generated_questions = generate_interview_questions(
            req,
            plan,
        )

        # Step 3: Store interview context for later phases.
        interviews[req.interview_id] = {
            "request": req,
            "plan": plan,
            "questions": generated_questions,
            "evaluations": {},
        }

        # Step 4: Return the generated questions.
        return InterviewStartResponse(
            questions=[
                question.model_dump()
                for question in generated_questions.questions
            ],
        )

    except Exception as error:
        logger.exception(
            "Interview generation failed. Error type: %s",
            type(error).__name__,
        )
        print("INTERVIEW START ERROR:", repr(error))

        raise HTTPException(
            status_code=502,
            detail=error_detail(
                "AI_FAILED",
                "Could not generate interview questions.",
            ),
        ) from error


# --------------------------------------------------
# 6. Evaluate interview answer
# --------------------------------------------------

@app.post(
    "/v1/interview/answer",
    response_model=InterviewAnswerResponse,
)
def evaluate_answer(req: InterviewAnswerRequest):

    # Step 1: Find the interview.
    interview = interviews.get(req.interview_id)

    if interview is None:
        raise HTTPException(
            status_code=404,
            detail=error_detail(
                "INTERVIEW_NOT_FOUND",
                "Interview not found.",
            ),
        )

    try:
        # Step 2: Evaluate the candidate's answer.
        evaluation = evaluate_interview_answer(
            req,
            interview,
        )

        return evaluation

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=error_detail(
                "INVALID_QUESTION",
                str(error),
            ),
        ) from error

    except Exception as error:
        logger.exception(
            "Interview answer evaluation failed. Error type: %s",
            type(error).__name__,
        )

        raise HTTPException(
            status_code=502,
            detail=error_detail(
                "AI_FAILED",
                "Could not evaluate interview answer.",
            ),
        ) from error


# --------------------------------------------------
# 7. Generate final interview report
# --------------------------------------------------

@app.post(
    "/v1/interview/report",
    response_model=FinalReportResponse,
)
def generate_report(req: FinalReportRequest):

    # Step 1: Find the interview.
    interview = interviews.get(req.interview_id)

    if interview is None:
        raise HTTPException(
            status_code=404,
            detail=error_detail(
                "INTERVIEW_CONTEXT_NOT_FOUND",
                "Interview context is not available. Please use the stored backend sections.",
            ),
        )

    try:
        # Step 2: Generate the final report.
        report = generate_final_report(
            req,
            interview,
        )

        return report

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=error_detail(
                "INVALID_INTERVIEW_DATA",
                str(error),
            ),
        ) from error

    except Exception as error:
        logger.exception(
            "Final interview report generation failed. Error type: %s",
            type(error).__name__,
        )

        raise HTTPException(
            status_code=502,
            detail=error_detail(
                "AI_FAILED",
                "Could not generate the final interview report.",
            ),
        ) from error


# --------------------------------------------------
# 8. Delete interview from memory
# --------------------------------------------------

@app.delete("/v1/interview/{interview_id}")
def delete_interview(interview_id: int):

    interviews.pop(interview_id, None)

    return {
        "message": "Interview data deleted successfully."
    }
