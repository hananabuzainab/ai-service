from app.question_generator import generate_interview_question


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
}

planned_question = {
    "question_id": 7,
    "category": "technical",
    "question_type": "problem-solving",
    "skill": "PostgreSQL",
    "difficulty": "medium",
    "primary_dimension": "problem_solving",
    "secondary_dimensions": ["technical_depth"],
    "evaluation_criteria": [
        "Identifies possible causes of a slow SQL query",
        "Explains how to investigate query performance",
        "Suggests appropriate optimization techniques",
    ],
}


question = generate_interview_question(
    interview_data,
    planned_question,
)

print(question.model_dump_json(indent=2))