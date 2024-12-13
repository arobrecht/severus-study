def preprocess_feedback(feedback: str):
    if feedback in ["+", "-"]:
        return {"feedback": True, "bc": feedback, "sub": None}
    elif feedback in ["None", None]:
        return {"feedback": False, "bc": None, "sub": None}
    else:
        typic_metrics = 0
        triple_in_question = preprocess_question_with_nlu(feedback)
        return {"feedback": True, "bc": None, "sub": [typic_metrics, triple_in_question]}


# For the simulation without nlu we don't need to process this
def preprocess_question_with_nlu(question: str):
    print(question)
    return question
