from app.interview_planner import create_interview_plan


interview_data = {
    "job_title": "Backend Developer",
    "job_description": """
    We need a junior backend developer with PHP,
    Laravel and MySQL experience.
    """,
    "resume_text": """
    Computer Engineering graduate with experience
    in Python, PHP and SQL.
    """,
    "matching_skills": [
        {
            "id": 1,
            "name": "php",
            "category": "languages",
            "importance": 1,
            "candidate_confidence": 1,
        }
    ],
    "missing_skills": [
        {
            "id": 2,
            "name": "laravel",
            "category": "frameworks",
            "importance": 0.95,
        },
        {
            "id": 3,
            "name": "mysql",
            "category": "databases",
            "importance": 0.75,
        },
    ],
}


plan = create_interview_plan(interview_data)

print(plan.model_dump_json(indent=2))