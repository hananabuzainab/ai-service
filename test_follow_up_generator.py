from app.follow_up_generator import generate_follow_up_question


interview_question = (
    "Could you describe a technical challenge you faced "
    "during one of your projects and explain how you resolved it?"
)

candidate_answer = "I used SQL indexes."

follow_up_reason = (
    "The answer is too short and does not explain "
    "the technical challenge or how SQL indexes were used."
)


question = generate_follow_up_question(
    interview_question,
    candidate_answer,
    follow_up_reason,
)

print(question.model_dump_json(indent=2))