
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


# --------------------------------------------------
# Application configuration
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

app = FastAPI(title="Sparr AI Service")


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
