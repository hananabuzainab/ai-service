
from app.final_evaluator import evaluate_final_interview


interview_data = {
    "job_title": "Junior Python Backend Developer",

    "job_description": """
    The role requires Python programming,
    problem-solving, and backend development.
    """,

    "resume_text": """
    Computer Engineering graduate.
    Worked on an academic graduation project
    involving Python and image processing.
    """,

    "matching_skills": [
        {"name": "Python"}
    ],

    "missing_skills": [],

    "plan": {
        "questions": [
            {
                "question_id": 1,
                "category": "behavioral",
                "skill": None,
                "primary_dimension": "problem_solving",
                "evaluation_criteria": [
                    "Describes a technical challenge",
                    "Explains troubleshooting steps",
                    "Describes the outcome"
                ]
            },
            {
                "question_id": 5,
                "category": "technical",
                "skill": "Python",
                "primary_dimension": "technical_depth",
                "evaluation_criteria": [
                    "Explains mutable and immutable types",
                    "Provides examples",
                    "Explains their behavior in functions"
                ]
            }
        ]
    },

    "answers": [
        {
            "question_id": 1,
            "question": "Describe a technical problem you faced.",
            "answer": "I had a problem with Python.",
            "is_follow_up": False,
            "evaluation": {}
        },
                {
            "question_id": 1,
            "question": "Could you explain how you solved it?",
            "answer": (
                "I used Python, OpenCV, NumPy, pandas, "
                "TensorFlow, and YOLO in my graduation project. "
                "I also worked with image processing, preprocessing, "
                "machine learning, and computer vision."
            ),
            "is_follow_up": True,
            "evaluation": {}
        },
        {
            "question_id": 5,
            "question": (
                "Explain mutable and immutable data types in Python."
            ),
        "answer": "I know Python basics.",
            "is_follow_up": False,
            "evaluation": {}
        }
    ]
}

print("\nFOLLOW-UP ANSWER ACTUALLY SENT:")
print(interview_data["answers"][1]["answer"])
result = evaluate_final_interview(interview_data)

print("\nFINAL EVALUATION:\n")
print(result.model_dump_json(indent=2))
