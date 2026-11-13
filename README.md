# Sparr AI Service

Sparr AI Service is a FastAPI service that provides AI-powered resume and job-description skill extraction, learning roadmaps, and structured technical interview workflows. It uses Google Gemini for language-model tasks and Pydantic schemas to validate inputs and outputs.

## Features

- Extract skills and confidence scores from PDF or TXT resumes.
- Extract required skills and importance scores from job descriptions.
- Normalize skill names, merge duplicates, and infer selected strongly related skills.
- Generate learning roadmaps for missing skills, with curated learning resources.
- Generate a structured interview plan containing 4 behavioral and 6 technical questions.
- Generate 10 interview questions and evaluate candidate answers.
- Generate a final interview report with a summary, improvement areas, four evaluation dimensions, and discrepancy flags.
- Delete an interview's in-memory context after the backend has safely stored the final report.

## Technology stack

- Python
- FastAPI
- Pydantic v2
- Google Gen AI SDK (Gemini)
- pdfplumber
- pytest

## Project structure

```text
ai-service/
├── app/
│   ├── main.py
│   ├── llm.py
│   ├── pdf_utils.py
│   ├── schemas.py
│   ├── skills_clean.py
│   ├── skill_rules.py
│   ├── resources.py
│   ├── roadmap.py
│   ├── roadmap_schemas.py
│   ├── interview_planner.py
│   ├── interview_plan_schemas.py
│   ├── interview_question_generator.py
│   ├── interview_generation_schemas.py
│   ├── interview_evaluator.py
│   ├── interview_schemas.py
│   ├── final_report_generator.py
│   └── final_report_schemas.py
├── prompts/
│   ├── extract_skills.py
│   ├── generate_roadmap.py
│   ├── plan_interview.py
│   ├── generate_interview_questions.py
│   ├── evaluate_interview_answer.py
│   └── generate_final_report.py
├── tests/
│   └── ...
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

The tree above describes the intended logical organization. The current repository may still keep test files at its root and test data in a differently named directory until the proposed organization is applied.

## Requirements

- Python 3.11 or newer (use the Python version supported by the pinned dependencies in `requirements.txt`).
- A Google Gemini API key.

## Installation

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-3.5-flash-lite
```

`GEMINI_API_KEY` is required when an endpoint makes a Gemini request. `LLM_MODEL` is optional; the service defaults to `gemini-3.5-flash-lite` when it is not provided. Never commit `.env` or expose API keys in source control.

## Run the service

From the project root, with the virtual environment activated:

```bash
uvicorn app.main:app --reload
```

The service is available at `http://127.0.0.1:8000`.

- Interactive API documentation: `http://127.0.0.1:8000/docs`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`
- Health check: `http://127.0.0.1:8000/health`

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Check service health. |
| `POST` | `/v1/extract-resume` | Extract resume text and skills. Accepts multipart form data with a `file` field. |
| `POST` | `/v1/extract-job` | Extract skills from a job description. |
| `POST` | `/v1/generate-roadmap` | Generate learning roadmaps for missing skills. |
| `POST` | `/v1/interview/start` | Generate the interview plan and 10 questions. |
| `POST` | `/v1/interview/answer` | Evaluate one candidate answer. |
| `POST` | `/v1/interview/report` | Generate the final interview report. |
| `DELETE` | `/v1/interview/{interview_id}` | Delete the interview context from AI-service memory. |

### 1. Health check

```http
GET /health
```

Example response:

```json
{"status": "ok"}
```

### 2. Extract resume skills

```http
POST /v1/extract-resume
Content-Type: multipart/form-data
```

Send the resume in a multipart field named `file`. Supported formats are PDF and UTF-8 TXT. Current limits are 5 MB, 30 PDF pages, and at least 50 extracted characters. Scanned/image-only PDFs are not supported because extraction uses the PDF text layer.

Example response shape:

```json
{
  "extracted_text": "Resume text...",
  "skills": [
    {
      "name": "python",
      "category": "languages",
      "confidence_score": 0.9
    }
  ]
}
```

### 3. Extract job-description skills

```http
POST /v1/extract-job
Content-Type: application/json
```

Example request:

```json
{
  "text": "We are looking for a Python developer with Django and SQL experience..."
}
```

Example response shape:

```json
{
  "skills": [
    {
      "name": "django",
      "category": "frameworks",
      "importance": 0.95
    }
  ]
}
```

### 4. Generate learning roadmaps

```http
POST /v1/generate-roadmap
Content-Type: application/json
```

Example request:

```json
{
  "job_title": "Backend Developer",
  "matching_skills": [
    {"name": "python"}
  ],
  "missing_skills": [
    {
      "id": 12,
      "name": "django",
      "category": "frameworks",
      "importance": 0.95
    }
  ]
}
```

The service sorts missing skills by importance and generates up to five roadmaps per request. If there are no missing skills, it returns an empty `roadmaps` array.

### 5. Start an interview

```http
POST /v1/interview/start
Content-Type: application/json
```

Example request:

```json
{
  "interview_id": 1001,
  "resume": "Candidate resume text with at least 50 characters...",
  "job_description": "Job description text with at least 20 characters...",
  "job_title": "Python Developer",
  "matching_skills": [
    {
      "id": 1,
      "name": "python",
      "category": "languages",
      "importance": 1.0,
      "candidate_confidence": 0.9
    }
  ],
  "missing_skills": [
    {
      "id": 2,
      "name": "django",
      "category": "frameworks",
      "importance": 0.95
    }
  ]
}
```

The service creates a plan with exactly 4 behavioral and 6 technical questions, then generates 10 main questions. The response contains a `questions` array; each item has `id`, `text`, and `type` (`main`).

### 6. Evaluate an interview answer

```http
POST /v1/interview/answer
Content-Type: application/json
```

Example request:

```json
{
  "interview_id": 1001,
  "id": 1,
  "text": "The candidate's answer to question 1..."
}
```

Example response:

```json
{
  "id": 1,
  "score": 8.5,
  "better_answer": "An improved answer grounded in the candidate's evidence..."
}
```

The service stores the original answer and its full internal evaluation in memory, keyed by question ID. Submitting the same question ID again replaces its previous stored answer and evaluation after a successful evaluation.

### 7. Generate the final interview report

```http
POST /v1/interview/report
Content-Type: application/json
```

The backend sends the interview ID, resume text, job description, and exactly 10 question records. Each question record contains:

- `question_id`
- `sequence_number`
- `question`
- `answer`
- `score`
- `better_answer`

The service verifies the submitted question text, answer, score, and better answer against its in-memory interview context before generating the report.

The response contains:

- `interview_id`
- `interview_summary` (`summary`, `strengths`, `job_relevance`)
- `improvement_areas` (`area`, `recommendation`)
- `dimension_scores` (exactly one each for `technical_depth`, `communication`, `domain_experience`, and `problem_solving`, each scored from 0 to 5)
- `discrepancy_flags` (`cv_claim`, `interview_claim`)

The complete request and response schemas are available through `/docs` and `/openapi.json`.

### 8. Delete interview context

```http
DELETE /v1/interview/1001
```

Call this endpoint only after the backend has successfully persisted the final report. The operation is idempotent: deleting an existing or already-deleted interview returns success.

## Error responses

Application errors use this general structure:

```json
{
  "detail": {
    "error": {
      "code": "ERROR_CODE",
      "message": "Human-readable explanation."
    }
  }
}
```

FastAPI request-validation errors may return its standard `422` response format. Common application status codes include `400` for invalid interview data, `404` for missing interview context, `422` for invalid or unsupported resume uploads, and `502` when an AI operation fails.

## Run tests

From the project root, with the dependencies installed:

```bash
pytest -q
```

The tests mock Gemini calls; they validate application logic and API behavior without requiring a live Gemini API request. Keep integration tests that call the real provider separate from the normal unit-test suite.

## Important runtime note

Interview state is currently stored in the AI service process memory, not in a database. The backend must:

1. Keep the same `interview_id` for all requests belonging to one interview.
2. Send the final report request while the AI service still has that interview context.
3. Persist the final report successfully.
4. Call `DELETE /v1/interview/{interview_id}` to release the stored memory.

Because the store is process-local, a service restart clears active interviews, and multiple application workers or replicas do not automatically share interview state. Use a shared persistent store if the deployment needs restart recovery or multi-worker scaling. Protect the service endpoints with the deployment's service-to-service authentication/network controls; this codebase does not implement API authentication itself.
