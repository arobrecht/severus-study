from severusStudy.snape.model_update.base_model_update import BaseFeedbackEvaluation


def test_feedback_evaluation_single_string():
    feedback_evaluation = BaseFeedbackEvaluation()
    feedback_evaluation.set_open_feedback_triple("(Player, play, Quarto)")
    triple = feedback_evaluation.preprocess_feedback_triples()
    assert triple == [['player', 'play', 'quarto']]


def test_feedback_evaluation_with_triple_list():
    feedback_evaluation = BaseFeedbackEvaluation()
    feedback_evaluation.set_open_feedback_triple(
        ["(Player, play, Quarto)?", "(Quarto, has, ?)", "(Player, ?, Quarto)"])
    triple = feedback_evaluation.preprocess_feedback_triples()
    print(triple)
    assert triple == [['player', 'play', 'quarto'], ['quarto', 'has', '?'], ['player', '?', 'quarto']]


def test_evaluate():
    feedback_evaluation = BaseFeedbackEvaluation()
    feedback_evaluation.set_open_feedback_triple(
        ["(Player, play, Quarto)?", "(Quarto, has, ?)", "(Player, ?, Quarto)"])
    feedback_evaluation.evaluate()
    assert feedback_evaluation.referred_feedback_triple == [['player', 'play', 'quarto'], ['quarto', 'has', '?'], ['player', '?', 'quarto']]


if __name__ == "__main__":
    test_feedback_evaluation_single_string()
    test_feedback_evaluation_with_triple_list()
    test_evaluate()
