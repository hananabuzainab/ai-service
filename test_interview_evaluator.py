from app.interview_evaluator import evaluate_interview_answer


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
    "question_id": 1,
    "category": "behavioral",
    "question_type": "experience",
    "skill": None,
    "difficulty": "medium",
    "primary_dimension": "problem_solving",
    "secondary_dimensions": ["communication"],
    "evaluation_criteria": [
        "Clearly describes a technical challenge",
        "Explains the specific troubleshooting steps taken",
        "Reflects on the final outcome and lessons learned",
    ],
}

question = (
    "Could you describe a technical challenge you faced "
    "during one of your projects and explain how you resolved it?"
)

answer = """
The application was slow because several queries
were repeatedly accessing the same data. I inspected
the queries, used JOINs to retrieve related data more
efficiently, and added indexes to columns used in
frequent searches. This improved response time.
"""

evaluation = evaluate_interview_answer(
    interview_data,
    planned_question,
    question,
    answer,
)

print(evaluation.model_dump_json(indent=2))