# Sparr AI Service

The AI service powering **Sparr**, a technical interview preparation platform for junior and mid-level software engineers.

Built with Python and FastAPI, this service integrates with Google Gemini to analyze resumes and job descriptions, extract and refine technical skills, generate prioritized learning roadmaps, conduct AI-powered technical interviews, evaluate candidate answers, and produce structured final interview assessments.

The service communicates with the Laravel backend through REST API endpoints and returns structured JSON responses.

---

## Core Workflow

The AI service supports two main workflows:

### 1. Resume and Job Analysis

1. **Resume Analysis:** Extracts text from PDF or TXT resumes and identifies the candidate's technical skills.
2. **Confidence Scoring:** Assigns each extracted resume skill a `confidence_score` between 0 and 1.
3. **Job Description Analysis:** Extracts technical requirements and assigns each skill an `importance` score between 0 and 1.
4. **Skill Refinement:** Normalizes skill names, resolves aliases, assigns categories, removes duplicates, and adds strongly implied related skills.
5. **Skill Matching:** The Laravel backend compares resume skills with job requirements to identify matched and missing skills.
6. **Roadmap Generation:** Receives matched and missing skills from Laravel and generates prioritized learning roadmaps for missing skills.

### 2. AI-Powered Interview

1. **Interview Initialization:** Receives the job title, job description, resume text, matching skills, and missing skills from the Laravel backend.
2. **Interview Planning:** Generates a structured interview plan containing 10 main questions: 4 behavioral and 6 technical.
3. **Question Generation:** Generates the first interview question based on the interview plan and candidate context.
4. **Answer Evaluation:** Evaluates each candidate answer against predefined evaluation criteria.
5. **Follow-up Questions:** Generates additional questions when an answer requires clarification or further assessment.
6. **Next Question:** Moves to the next planned main question when no follow-up is required.
7. **Final Evaluation:** Evaluates the candidate's demonstrated skills and four interview dimensions after all 10 main questions are completed.
8. **Result Delivery:** Returns the final evaluation to the Laravel backend in the response to the final answer.

---

## Features

### Resume and Job Analysis

- Extract technical skills from PDF and TXT resumes.
- Extract technical requirements from job descriptions.
- Assign confidence scores to resume skills.
- Assign importance scores to job requirements.
- Normalize skill names using aliases and canonical names.
- Categorize skills into predefined technical categories.
- Infer strongly related skills using predefined relationships.
- Merge duplicate skills while preserving the highest valid score.

### Learning Roadmaps

- Generate prioritized, skill-specific learning roadmaps.
- Consider the candidate's existing skills when generating learning plans.
- Generate up to 5 roadmaps per request.
- Generate up to 6 weekly learning steps per roadmap.
- Retrieve learning resources separately through the resources module.

### AI Interview

- Generate structured interview plans containing 10 main questions.
- Include 4 behavioral and 6 technical questions.
- Define question type, target skill, difficulty, evaluation dimensions, and criteria.
- Generate interview questions using candidate and job context.
- Evaluate candidate answers individually.
- Generate follow-up questions when additional clarification is needed.
- Support up to 3 follow-up questions per interview, with at most one per main question.
- Maintain the main question ID while asking its follow-up questions.
- Generate a final evaluation based on the complete interview, including follow-up answers.
- Assess candidate skills and four interview dimensions.
- Identify strengths, improvement areas, and discrepancies between resume claims and interview evidence.

### General

- Validate API requests and responses using Pydantic.
- Integrate with Google Gemini through the `google-genai` SDK.
- Provide a health-check endpoint.
- Return structured JSON responses.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Check service availability |
| `POST` | `/v1/extract-resume` | Extract resume text and technical skills |
| `POST` | `/v1/extract-job` | Extract technical requirements from a job description |
| `POST` | `/v1/generate-roadmap` | Generate prioritized learning roadmaps |
| `POST` | `/v1/interview/start` | Initialize an interview and generate the first question |
| `POST` | `/v1/interview/answer` | Evaluate an answer and return a follow-up, next question, or final evaluation |

Interactive API documentation is available at:

`http://127.0.0.1:8000/docs`

---

# Part 1: Resume and Job Analysis

## 1. Resume Skills Extraction

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

### Confidence Score

The `confidence_score` represents how clearly the resume demonstrates a candidate's knowledge or use of a skill.

It ranges from 0 to 1. The scoring considers:

- Whether the skill appears in the resume's skills section.
- Whether it is demonstrated in projects or work experience.
- The stated proficiency level.
- Whether the skill is explicitly mentioned or strongly implied.

Strongly implied skills receive a maximum confidence score of 0.85.

## 2. Job Description Skills Extraction

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

### Importance Score

The `importance` score represents how important a skill is for the target job.

It ranges from 0 to 1 and considers:

- Core and must-have requirements.
- Skills mentioned in the job title.
- Required experience and repeated mentions.
- Preferred and nice-to-have skills.
- Skills mentioned only in passing.

If the model returns a missing or invalid importance score, the service uses a default value of `0.5`.

## 3. Skill Refinement and Normalization

Before returning extracted skills, the service applies a refinement pipeline.

### Alias Normalization

Common alternative names are mapped to canonical names.

| Input | Normalized name |
|---|---|
| JS | JavaScript |
| TS | TypeScript |
| Postgres | PostgreSQL |
| NodeJS | Node.js |
| ReactJS | React |
| sklearn | scikit-learn |
| GCP | Google Cloud Platform |

### Related Skill Inference

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

### Duplicate Handling

- Duplicate skills are merged.
- The highest valid score is preserved.
- Invalid skill entries are skipped.
- Skill names are normalized and validated.
- Unknown categories are mapped to `other`.

### Supported Categories

| Category | Description |
|---|---|
| `languages` | Programming, markup, and query languages |
| `frameworks` | Frameworks, libraries, and runtimes |
| `databases` | Database technologies |
| `cloud_devops` | Cloud, containers, DevOps, and related technologies |
| `ml_data` | Machine learning and data technologies |
| `tools` | Development and technical tools |
| `other` | Other technical skills and concepts |

## 4. Skill Matching

Skill comparison is handled by the Laravel backend, not by this service.

The backend compares the extracted resume skills with the job description requirements and identifies:

- **Matched Skills:** Skills found in both the candidate's resume and job requirements.
- **Missing Skills:** Skills required by the job that are not found in the candidate's resume.

The backend then sends the matching and missing skills to the AI service for roadmap generation and interview initialization.

## 5. Learning Roadmap Generation

`POST /v1/generate-roadmap`

Generates personalized learning roadmaps for missing skills based on the target job and the candidate's existing knowledge.

### Request Structure

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

### Roadmap Generation Process

1. Receives the target job title, matching skills, and missing skills.
2. Sorts missing skills by importance in descending order.
3. Selects up to 5 skills for roadmap generation.
4. Sends each selected skill to Gemini with the job title and known skills as context.
5. Generates a learning plan containing up to 6 weekly steps.
6. Cleans and validates the generated steps.
7. Retrieves learning resources separately through the resources module.
8. Returns all generated roadmaps in a structured JSON response.

### Roadmap Response Structure

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

### Roadmap Design Rules

- Each roadmap focuses on one missing skill.
- Each roadmap contains up to 6 weekly steps.
- Each step includes a title and up to 5 topics.
- The plan progresses from fundamentals to a practical portfolio project.
- The candidate's known skills are considered when generating the learning plan.
- Learning resources are retrieved separately from the LLM-generated steps.
- If no missing skills are provided, the service returns an empty `roadmaps` list.

---

# Part 2: AI-Powered Interview

## 1. Interview Overview

The interview workflow is designed to conduct a text-based technical interview based on the candidate's resume and the target job requirements.

The Laravel backend sends the required interview context to the AI service. The AI service generates the interview plan, asks questions, evaluates answers, and produces a final assessment.

The interview contains:

- 10 main questions.
- 4 behavioral questions.
- 6 technical questions.
- Up to 3 follow-up questions across the interview.
- A final evaluation after completion.

## 2. Interview Initialization

`POST /v1/interview/start`

Initializes a new interview session.

### Request Structure

```json
{
  "job_title": "Backend Developer",
  "job_description": "We are looking for a junior backend developer...",
  "resume_text": "Computer Engineer with experience in Python...",
  "matching_skills": [
    {
      "id": 1,
      "name": "python",
      "category": "languages",
      "importance": 0.9,
      "candidate_confidence": 0.9
    }
  ],
  "missing_skills": [
    {
      "id": 12,
      "name": "django",
      "category": "frameworks",
      "importance": 0.95,
      "candidate_confidence": null
    }
  ]
}
```

The `matching_skills` and `missing_skills` fields contain the skills identified by the backend's skill-matching process.

### Interview Initialization Process

1. Validates the incoming interview data.
2. Creates a structured interview plan containing 10 main questions.
3. Assigns each question a category, type, target skill, difficulty, evaluation dimensions, and evaluation criteria.
4. Generates the first interview question.
5. Creates a unique `interview_id`.
6. Initializes the interview state.
7. Returns the first question to the backend.

### Example Response

```json
{
  "status": "started",
  "interview_id": "abc-123",
  "question_id": 1,
  "question": "Can you explain your experience with Python?"
}
```

The example values are illustrative.

## 3. Interview Planning

The interview planner generates exactly 10 main questions.

### Question Distribution

| Category | Number of questions |
|---|---:|
| Behavioral | 4 |
| Technical | 6 |
| **Total** | **10** |

Each planned question includes:

- `question_id`: Main question identifier.
- `category`: Behavioral or technical.
- `question_type`: The intended question format.
- `skill`: Target technical skill, when applicable.
- `difficulty`: Easy, medium, or hard.
- `primary_dimension`: Main evaluation dimension.
- `secondary_dimensions`: Additional evaluation dimensions.
- `evaluation_criteria`: Criteria used to evaluate the answer.

The planner aims to cover different relevant skills and avoid unnecessary repetition.

## 4. Answer Submission and Evaluation

`POST /v1/interview/answer`

Receives a candidate's answer and evaluates it against the current question.

### Request Structure

```json
{
  "interview_id": "abc-123",
  "question_id": 1,
  "request_id": "req-001",
  "answer": "I used Python to build REST APIs and process data."
}
```

### Request Fields

| Field | Description |
|---|---|
| `interview_id` | Identifies the active interview session |
| `question_id` | Identifies the current main question |
| `request_id` | Unique identifier for the answer submission |
| `answer` | Candidate's text answer |

### Answer Evaluation Process

1. Validates the interview ID and question ID.
2. Checks request ID handling to prevent duplicate processing.
3. Evaluates the candidate's answer against the question's evaluation criteria.
4. Extracts supporting evidence from the answer.
5. Identifies strengths and improvement areas.
6. Determines whether a follow-up question is needed.
7. Returns the appropriate next step.

### Evaluation Structure

Each answer evaluation includes:

- `criteria_results`: Evaluation results for individual criteria.
- `status`: Whether a criterion is met, partially met, not met, or lacks sufficient evidence.
- `evidence`: Evidence supporting the criterion result.
- `strengths`: Demonstrated strengths.
- `improvements`: Areas that need improvement.
- `needs_follow_up`: Indicates whether clarification is needed.
- `follow_up_reason`: Explains why a follow-up may be required.

## 5. Follow-up Questions

Follow-up questions are generated when the candidate's answer needs clarification or further assessment.

### Follow-up Rules

- A follow-up question is linked to its original main question.
- The main `question_id` remains unchanged during follow-up questions.
- A maximum of one follow-up question is allowed per main question.
- A maximum of three follow-up questions is allowed across the entire interview.
- Follow-up answers are evaluated like other answers.
- Follow-up questions do not count toward the 10 main questions.

### Example Follow-up Response

```json
{
  "is_follow_up": true,
  "question_id": 1,
  "question": "Can you explain how you handled API errors?",
  "evaluation": {
    "criteria_results": [],
    "strengths": [],
    "improvements": [],
    "needs_follow_up": false,
    "follow_up_reason": null
  }
}
```

The example values are illustrative.

## 6. Moving to the Next Main Question

If no follow-up is required, the service generates the next question from the previously created interview plan.

### Example Response

```json
{
  "is_follow_up": false,
  "interview_completed": false,
  "next_question_id": 2,
  "question": "Describe a challenging situation you faced while working on a project.",
  "evaluation": {
    "criteria_results": [],
    "strengths": [],
    "improvements": [],
    "needs_follow_up": false,
    "follow_up_reason": null
  }
}
```

The example values are illustrative.

The main question ID advances only when the service moves to the next planned question. Follow-up questions retain the original main question ID.

## 7. Final Interview Evaluation

After the candidate completes all 10 main questions, the service generates a comprehensive final evaluation.

The final evaluation considers all main answers and their associated follow-up answers.

It assesses the candidate across two areas:

### A. Skill Assessments

Evaluates technical skills demonstrated during the interview.

Each skill assessment includes:

- `skill_name`: Name of the assessed skill.
- `score`: Score from 0 to 5, or null when evidence is insufficient.
- `evidence`: Evidence from the candidate's answers.
- `question_ids`: Main question IDs associated with the evidence.

### B. Interview Dimension Assessments

The candidate is assessed across four dimensions:

| Dimension | Description |
|---|---|
| `technical_depth` | Depth of technical knowledge and understanding |
| `communication` | Ability to explain ideas clearly |
| `domain_experience` | Relevant experience in the job domain |
| `problem_solving` | Ability to analyze and solve problems |

Each dimension receives a score from 0 to 5, or null when there is insufficient evidence.

### C. Additional Evaluation Results

The final evaluation also includes:

- `strengths`: Candidate's demonstrated strengths.
- `improvements`: Areas that need further development.
- `discrepancies`: Differences between claims in the resume and evidence demonstrated during the interview.

The evaluation is evidence-based. Skills mentioned in the resume are not automatically considered proven unless supported by interview evidence.

The service does not generate a single overall candidate score.

### Final Evaluation Response

The final evaluation is returned within the response to the candidate's last answer.

Example:

```json
{
  "interview_completed": true,
  "evaluation": {
    "criteria_results": [],
    "strengths": [],
    "improvements": [],
    "needs_follow_up": false,
    "follow_up_reason": null
  },
  "final_evaluation": {
    "skill_assessments": [
      {
        "skill_name": "python",
        "score": 4.0,
        "evidence": [
          "Demonstrated practical experience building REST APIs."
        ],
        "question_ids": [1, 5]
      }
    ],
    "dimension_assessments": [
      {
        "dimension": "technical_depth",
        "score": 4.0,
        "evidence": [],
        "question_ids": [1, 3]
      },
      {
        "dimension": "communication",
        "score": 4.0,
        "evidence": [],
        "question_ids": [2, 4]
      },
      {
        "dimension": "domain_experience",
        "score": 3.0,
        "evidence": [],
        "question_ids": [5, 6]
      },
      {
        "dimension": "problem_solving",
        "score": 4.0,
        "evidence": [],
        "question_ids": [7, 8]
      }
    ],
    "strengths": [],
    "improvements": [],
    "discrepancies": []
  },
  "message": "Interview completed successfully."
}
```

The example values are illustrative and do not represent actual model output.

---

## 8. Interview State and Storage

The current implementation maintains interview state in an in-memory Python dictionary:

```python
interviews = {}
```

The state includes information required to continue an interview, such as:

- Interview request context.
- Interview plan.
- Current question.
- Candidate answers.
- Follow-up count.
- Follow-up usage per main question.
- Processed request information.

### Current Limitation

In-memory interview state is temporary. It is lost when the AI service process restarts.

The Laravel backend can store the questions, answers, evaluations, and final results it receives from the AI service.

However, the current AI service implementation still relies on its own in-memory interview state to continue an active interview.

**The final storage architecture and responsibility for interview-state management between Laravel and the AI service are subject to backend integration agreement.**

---

## 9. Request Handling and Error Responses

The interview answer endpoint validates the interview and request identifiers before processing an answer.

Important request-handling rules:

- `interview_id` identifies the interview session.
- `question_id` identifies the current main question.
- `request_id` identifies a specific answer submission.
- Reusing the same `request_id` is intended for retrying the exact same request after a network issue.
- Reusing a request ID with different request data returns `409 REQUEST_ID_CONFLICT`.

The service also validates the current interview and question state before accepting an answer.

For exact error response formats and status codes, refer to the API implementation and the interactive API documentation at `/docs`.

---

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

## Running Tests

Run the automated test suite using:

```bash
pytest -v
```

---

## Project Structure

The AI service is organized into application modules, LLM prompts, automated tests, and test data.

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
│   ├── skills_clean.py
│   ├── interview_schemas.py
│   ├── interview_plan_schemas.py
│   ├── interview_planner.py
│   ├── question_generator.py
│   ├── interview_evaluator.py
│   ├── follow_up_generator.py
│   ├── final_evaluator.py
│   └── final_evaluation_schemas.py
│
├── prompts/
│   ├── __init__.py
│   ├── extract_skills.py
│   ├── generate_roadmap.py
│   ├── plan_interview.py
│   ├── generate_interview_question.py
│   ├── evaluate_interview_answer.py
│   ├── generate_follow_up.py
│   └── evaluate_final_interview.py
│
├── tsts/
│   ├── __init__.py
│   └── data/
│       ├── job.txt
│       └── resume_jack.pdf
│
├── test_final_evaluator.py
├── test_final_evaluator_discrepancy.py
├── test_final_evaluator_jargon.py
├── test_final_evaluator_wrong_answer.py
├── test_follow_up_generator.py
├── test_interview_evaluator.py
├── test_interview_planner.py
├── test_llm.py
├── test_main.py
├── test_pdf_utils.py
├── test_question_generator.py
├── test_roadmap.py
├── test_roadmap_api.py
├── test_schemas.py
├── test_skills_clean.py
├── test_skill_rules.py
│
├── .env
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

### Application Modules

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI application and API endpoints |
| `llm.py` | Google Gemini integration and structured LLM responses |
| `pdf_utils.py` | Resume file validation and text extraction |
| `resources.py` | Learning resource retrieval |
| `roadmap.py` | Learning roadmap generation and processing |
| `roadmap_schemas.py` | Roadmap request and response validation |
| `schemas.py` | Resume extraction, job extraction, and skill schemas |
| `skill_rules.py` | Skill aliases and predefined skill relationships |
| `skills_clean.py` | Skill normalization, categorization, inference, and deduplication |
| `interview_schemas.py` | Interview request and response schemas |
| `interview_plan_schemas.py` | Interview plan and question schemas |
| `interview_planner.py` | Creates the structured interview plan |
| `question_generator.py` | Generates the planned interview questions |
| `interview_evaluator.py` | Evaluates individual candidate answers |
| `follow_up_generator.py` | Generates follow-up questions when clarification is needed |
| `final_evaluator.py` | Generates the final interview assessment |
| `final_evaluation_schemas.py` | Validates final evaluation data structures |

### Prompt Modules

The `prompts/` directory contains the instructions provided to Gemini for different AI tasks:

- `extract_skills.py`: Resume and job description skill extraction.
- `generate_roadmap.py`: Learning roadmap generation.
- `plan_interview.py`: Structured interview planning.
- `generate_interview_question.py`: Main interview question generation.
- `evaluate_interview_answer.py`: Candidate answer evaluation.
- `generate_follow_up.py`: Follow-up question generation.
- `evaluate_final_interview.py`: Final interview evaluation.

### Automated Tests

The `test_*.py` files contain automated tests covering:

- Resume and job skill extraction.
- Skill normalization and refinement.
- PDF processing and validation.
- LLM integration.
- Roadmap generation and API behavior.
- Interview planning and question generation.
- Candidate answer evaluation.
- Follow-up question generation.
- Final interview evaluation, including discrepancies, technical jargon, and incorrect answers.
- API endpoints and request validation.

### Test Data

The `tsts/data/` directory contains sample files used during testing:

- `job.txt`: Sample job description.
- `resume_jack.pdf`: Sample candidate resume.

### Configuration Files

- `.env`: Local environment variables and API credentials. Must not be committed to Git.
- `.env.example`: Example environment configuration.
- `.gitignore`: Files and directories excluded from version control.
- `requirements.txt`: Python project dependencies.


---

## Technologies

- **Python** – Core programming language.
- **FastAPI** – REST API framework.
- **Google Gemini (`google-genai`)** – LLM integration.
- **Pydantic** – Data validation and API schemas.
- **pdfplumber** – PDF text extraction.
- **Pytest** – Automated testing.

---

## Responsibilities and Integration

The AI service is responsible for:

- Resume and job description skill extraction.
- Skill normalization and refinement.
- Learning roadmap generation.
- Interview planning and question generation.
- Candidate answer evaluation.
- Follow-up question generation.
- Final interview assessment.

The Laravel backend is responsible for:

- Managing the main application workflow.
- Managing candidate and job data.
- Comparing extracted resume skills with job requirements.
- Sending the required context to the AI service.
- Receiving AI-generated questions and evaluation results.
- Persisting interview data and managing its presentation.

The exact interview-state storage and data-exchange approach must be agreed upon during backend integration.

---

## Current Limitations

- Scanned image-only PDFs are not supported because OCR is not implemented.
- Skill extraction and scoring may vary between model responses.
- Roadmap quality and availability depend on the Gemini API.
- Skill matching is handled by the Laravel backend.
- Interview state is currently stored in memory and is lost when the service restarts.
- Adaptive question generation based on previous candidate answers is not currently implemented.
- Authentication and Docker deployment are not implemented in this service.
- The final interview storage architecture is still subject to backend integration agreement.