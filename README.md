# Sparr AI Service

The AI service powering **Sparr**, a technical interview preparation platform for junior and mid-level software engineers.

Built with Python and FastAPI, the service integrates with Google Gemini to analyze resumes and job descriptions, extract and evaluate technical skills, refine skill data, and generate prioritized learning roadmaps for skills required by a target job.

The service communicates with the Laravel backend and returns structured JSON responses.

## Core Workflow

1. **Resume Analysis:** Extracts text from PDF or TXT resumes and identifies the candidate's technical skills.
2. **Confidence Scoring:** Assigns each extracted resume skill a `confidence_score` between 0 and 1, based on how clearly the resume demonstrates that skill.
3. **Job Description Analysis:** Extracts technical requirements and assigns each skill an `importance` score between 0 and 1 based on its relevance to the target role.
4. **Skill Refinement:** Normalizes skill names, resolves aliases, assigns categories, removes duplicates, and adds strongly implied related skills.
5. **Skill Matching:** The Laravel backend compares resume skills with job requirements to identify matched and missing skills.
6. **Roadmap Generation:** Receives matched and missing skills from Laravel and generates prioritized learning roadmaps for missing skills.

## Features

- Extract technical skills from PDF and TXT resumes.
- Extract technical requirements from job descriptions.
- Assign confidence scores to resume skills.
- Assign importance scores to job requirements.
- Normalize skill names using aliases and canonical names.
- Categorize skills into predefined technical categories.
- Infer strongly related skills using predefined relationships.
- Merge duplicate skills while preserving the highest valid score.
- Generate prioritized, skill-specific learning roadmaps.
- Provide curated learning resources for roadmap skills.
- Validate API requests and responses using Pydantic.
- Provide a health-check endpoint.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Check service availability |
| `POST` | `/v1/extract-resume` | Extract resume text and technical skills with confidence scores |
| `POST` | `/v1/extract-job` | Extract job skills with importance scores |
| `POST` | `/v1/generate-roadmap` | Generate prioritized learning roadmaps for missing skills |

### 1. Resume Skills Extraction

`POST /v1/extract-resume`

Accepts a resume through `multipart/form-data`.

- Field name: `file`
- Supported formats: PDF and TXT
- Maximum file size: 5 MB

Example response:

```json
{
  "extracted_text": "Backend developer with Python experience...",
  "skills": [
    {
      "name": "python",
      "category": "languages",
      "confidence_score": 0.95
    },
    {
      "name": "django",
      "category": "frameworks",
      "confidence_score": 0.85
    }
  ]
}
```

**Confidence score**

The `confidence_score` represents how clearly the resume demonstrates a candidate's knowledge or use of a skill.

It ranges from 0 to 1. The scoring considers:
- Whether the skill appears in the resume's skills section.
- Whether it is demonstrated in projects or work experience.
- The stated proficiency level.
- Whether the skill is explicitly mentioned or strongly implied.

Strongly implied skills receive a maximum confidence score of 0.85.

### 2. Job Description Skills Extraction

`POST /v1/extract-job`

Accepts a job description as JSON.

Example request:

```json
{
  "text": "Backend Developer. Requirements: Python, SQL, Docker, Git."
}
```

Example response:

```json
{
  "skills": [
    {
      "name": "python",
      "category": "languages",
      "importance": 1.0
    },
    {
      "name": "sql",
      "category": "languages",
      "importance": 0.8
    }
  ]
}
```

**Importance score**

The `importance` score represents how important a skill is for the target job.

It ranges from 0 to 1 and considers:
- Core and must-have requirements.
- Skills mentioned in the job title.
- Required experience and repeated mentions.
- Preferred and nice-to-have skills.
- Skills mentioned only in passing.

If the model returns a missing or invalid importance score, the service uses a default value of `0.5`.

### 3. Skill Refinement and Normalization

Before returning extracted skills, the service applies a refinement pipeline.

**Alias normalization**

Common alternative names are mapped to canonical names.

Examples:

| Input | Normalized name |
|---|---|
| JS | JavaScript |
| TS | TypeScript |
| Postgres | PostgreSQL |
| NodeJS | Node.js |
| ReactJS | React |
| sklearn | scikit-learn |
| GCP | Google Cloud Platform |

**Related skill inference**

The service uses predefined strong relationships to add clearly related skills.

Examples:
- Django → Python
- FastAPI → Python
- PostgreSQL → SQL
- Laravel → PHP
- Express → Node.js
- Docker Compose → Docker
- GitHub Actions → CI/CD

Inferred resume skills have their confidence score capped at 0.85. Explicitly extracted skills retain their original scores.

**Duplicate handling**

- Duplicate skills are merged.
- The highest valid score is preserved.
- Invalid skill entries are skipped.
- Skill names are normalized and validated.
- Unknown categories are mapped to `other`.

**Supported categories**

| Category | Description |
|---|---|
| `languages` | Programming, markup, and query languages |
| `frameworks` | Frameworks, libraries, and runtimes |
| `databases` | Database technologies |
| `cloud_devops` | Cloud, containers, DevOps, and related technologies |
| `ml_data` | Machine learning and data technologies |
| `tools` | Development and technical tools |
| `other` | Other technical skills and concepts |

### 4. Skill Matching

Skill comparison is handled by the Laravel backend, not by this service.

The backend compares the extracted resume skills with the job description requirements and identifies:

- **Matched Skills:** Skills found in both the candidate's resume and job requirements.
- **Missing Skills:** Skills required by the job that are not found in the candidate's resume.

The backend then sends the matching and missing skills to the AI service for roadmap generation.

### 5. Learning Roadmap Generation

`POST /v1/generate-roadmap`

Generates personalized learning roadmaps for missing skills based on the target job and the candidate's existing knowledge.

**Request structure**

```json
{
  "job_title": "Backend Developer",
  "matching_skills": [
    {
      "name": "python"
    },
    {
      "name": "sql"
    }
  ],
  "missing_skills": [
    {
      "id": 12,
      "name": "django",
      "category": "frameworks",
      "importance": 0.9
    }
  ]
}
```

**Roadmap generation process**

1. Receives the target job title, matching skills, and missing skills.
2. Sorts missing skills by importance in descending order.
3. Selects up to 5 skills for roadmap generation.
4. Sends each selected skill to Gemini with the job title and known skills as context.
5. Generates a learning plan containing up to 6 weekly steps.
6. Cleans and validates the generated steps.
7. Retrieves learning resources separately through the resources module.
8. Returns all generated roadmaps in a structured JSON response.

**Roadmap response structure**

```json
{
  "roadmaps": [
    {
      "skill_id": 12,
      "skill_name": "django",
      "category": "frameworks",
      "importance": 0.9,
      "priority": 1,
      "title": "Learning roadmap: django",
      "estimated_duration": "4 weeks",
      "steps": [
        {
          "week": 1,
          "title": "Django Fundamentals",
          "topics": [
            "Project structure",
            "Models and migrations",
            "URL routing",
            "Views"
          ]
        }
      ],
      "resources": [
        {
          "title": "Resource title",
          "url": "https://example.com"
        }
      ]
    }
  ]
}
```

The example values are illustrative.

**Roadmap design rules**

- Each roadmap focuses on one missing skill.
- Each roadmap contains up to 6 weekly steps.
- Each step includes a title and up to 5 topics.
- The plan progresses from fundamentals to a practical portfolio project.
- The candidate's known skills are considered when generating the learning plan.
- Learning resources are retrieved separately from the LLM-generated steps.
- If no missing skills are provided, the service returns an empty `roadmaps` list.

## Environment Requirements

- Python 3.14
- Google Gemini API key

## Installation

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

Configure the `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-3.5-flash-lite
```

Never commit `.env` or expose your API key.

## Running the Service

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
│   ├── skill_rules.py
│   └── skills_clean.py
├── prompts/
│   ├── __init__.py
│   ├── extract_skills.py
│   └── generate_roadmap.py
├── tsts/
│   ├── __init__.py
│   └── data/
├── test_llm.py
├── test_main.py
├── test_pdf_utils.py
├── test_roadmap.py
├── test_roadmap_api.py
├── test_schemas.py
├── test_skill_rules.py
├── test_skills_clean.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Technologies

- **Python** – Core programming language.
- **FastAPI** – REST API framework.
- **Google Gemini (`google-genai`)** – LLM integration.
- **Pydantic** – Data validation and API schemas.
- **pdfplumber** – PDF text extraction.
- **Pytest** – Automated testing.

## Current Limitations

- Scanned image-only PDFs are not supported because OCR is not implemented.
- Skill extraction and scoring may vary between model responses.
- Roadmap quality and availability depend on the Gemini API.
- Skill matching is handled by the Laravel backend.
- Authentication and Docker deployment are not implemented in this service.
