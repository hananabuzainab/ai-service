# Sparr AI Service

A Python FastAPI service for **Sparr**, a platform that helps junior and mid-level software engineers prepare for technical interviews based on their resumes and target job descriptions.

The service is called by the Laravel backend. It uses Google Gemini to extract technical skills from resumes and job descriptions, and generate learning roadmaps for missing skills.

## Features

- Extract technical skills from PDF and TXT resumes.
- Extract required technical skills from job descriptions.
- Normalize and categorize extracted skills.
- Generate prioritized learning roadmaps for missing skills.
- Provide a health-check endpoint.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Check service status |
| `POST` | `/v1/extract-resume` | Extract text and skills from a resume |
| `POST` | `/v1/extract-job` | Extract skills from a job description |
| `POST` | `/v1/generate-roadmap` | Generate learning roadmaps for missing skills |

### 1. Extract Resume Skills

`POST /v1/extract-resume`

- Content type: `multipart/form-data`
- Field: `file`
- Supported formats: PDF and TXT
- Maximum file size: 5 MB

Example response:

```json
{
  "extracted_text": "Backend developer with Python experience...",
  "skills": [
    { "name": "python", "category": "languages" },
    { "name": "docker", "category": "cloud_devops" }
  ]
}
```

### 2. Extract Job Skills

`POST /v1/extract-job`

Request:

```json
{
  "text": "Backend Developer. Requirements: Python, SQL, Docker, Git."
}
```

Example response:

```json
{
  "skills": [
    { "name": "python", "category": "languages" },
    { "name": "sql", "category": "languages" }
  ]
}
```

### 3. Generate Learning Roadmaps

`POST /v1/generate-roadmap`

Generates prioritized learning roadmaps for missing skills, using the candidate's matching skills and target job title as context.

The request includes:
- `job_title`
- `missing_skills`
- `matching_skills`

The service generates a maximum of 5 roadmaps per request.

### 4. Health Check

`GET /health`

Example response:

```json
{
  "status": "ok"
}
```

## Requirements

- Python 3.14
- Google Gemini API key

## Project Setup

### Windows

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and configure the environment variables.

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key |
| `LLM_MODEL` | Gemini model name. Defaults to `gemini-3.5-flash-lite` |

Never commit your `.env` file or expose your API key.

## Run the Service

```bash
uvicorn app.main:app --reload
```

Interactive API documentation:

`http://127.0.0.1:8000/docs`

## Project Structure

```text
ai-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── llm.py
│   ├── pdf_utils.py
│   ├── resources.py
│   ├── roadmap.py
│   ├── roadmap_schemas.py
│   ├── schemas.py
│   ├── skills_clean.py
│   └── skill_rules.py
├── prompts/
│   ├── __init__.py
│   ├── extract_skills.py
│   └── generate_roadmap.py
├── tests/
├── tsts/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Technologies

- Python
- FastAPI
- Google Gemini API (`google-genai`)
- Pydantic
- pdfplumber
- Pytest

## Current Limitations

- Scanned image-only PDFs are not supported (OCR is not implemented).
- Skill extraction may vary between model responses.
- Roadmap generation depends on the Gemini API response and availability.
- Docker deployment and authentication are not implemented yet.
