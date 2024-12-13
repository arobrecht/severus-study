from abc import abstractmethod

import numpy as np

from severusStudy.snape.solver.triple_action import ActionType


class FeedbackSimulator:
    """
    This class is the abstract class to simulate feedback. Different Harry Potter characters can be chosen.
    """
    prob_substantive_feedback: float
    prob_bc_feedback: float
    prob_no_feedback: float
    prob_pos_feedback: float
    prob_neg_feedback: float

    def __init__(self):
        self.random_generator = np.random.default_rng()

    @abstractmethod
    def set_probabilities(self):
        pass

    def get_feedback(self, last_action):
        """
        Simulates a feedback which can be used in the study_simulation
        Returns:
            a dictionary with the feedback options
        """
        feedback_mode = self.random_generator.choice(['sub', 'bc', 'no'],
                                                     p=[self.prob_substantive_feedback, self.prob_bc_feedback,
                                                        self.prob_no_feedback])
        feedback = {"feedback": False, "bc": None, "sub": None}
        # We don't want to give feedback on structure moves
        if last_action.action_type in [ActionType.STRUCTURE_BRIDGING, ActionType.STRUCTURE_MENTALIZE,
                                       ActionType.STRUCTURE_SUMMARIZE, ActionType.STRUCTURE_COMPREHENSION]:
            return feedback
        if feedback_mode == 'sub':
            # Randomly decide which kind of question is asked
            feedback["feedback"] = True
            last_action_triple = last_action.triple
            triple_components = last_action_triple.split(' ')
            random_number = self.random_generator.choice([0, 1, 2, 3], p=[1 / 4, 1 / 4, 1 / 4, 1 / 4])
            if random_number != 3:
                triple_components[random_number] = "?"
            # The first element here is the metrics we used for the typing/deleting behaviour
            # normally, we would use the preprocess feedback function
            feedback["sub"] = [0, " ".join(triple_components)]
            random_tae = self.random_generator.choice(["lower", "higher", "None"], p=[1 / 4, 1 / 4, 1 / 2])
            feedback["tae"] = random_tae
            return feedback
        if feedback_mode == 'bc':
            feedback["feedback"] = True
            feedback["bc"] = self.random_generator.choice(['+', '-'],
                                                          p=[self.prob_pos_feedback, self.prob_neg_feedback])
            return feedback
        else:
            return feedback


class Ron(FeedbackSimulator):
    def __init__(self):
        super(Ron, self).__init__()
        self.set_probabilities()

    def set_probabilities(self):
        self.prob_substantive_feedback = 0.1
        self.prob_bc_feedback = 0.25
        self.prob_no_feedback = 0.65
        self.prob_pos_feedback = 0.2
        self.prob_neg_feedback = 1 - self.prob_pos_feedback


class Draco(FeedbackSimulator):
    def __init__(self):
        super(Draco, self).__init__()
        self.set_probabilities()

    def set_probabilities(self):
        self.prob_substantive_feedback = 0.3
        self.prob_bc_feedback = 0.4
        self.prob_no_feedback = 0.3
        self.prob_pos_feedback = 0.6
        self.prob_neg_feedback = 1 - self.prob_pos_feedback


class Hermine(FeedbackSimulator):
    def __init__(self):
        super(Hermine, self).__init__()
        self.set_probabilities()

    def set_probabilities(self):
        self.prob_substantive_feedback = 0.4
        self.prob_bc_feedback = 0.5
        self.prob_no_feedback = 0.1
        self.prob_pos_feedback = 0.9
        self.prob_neg_feedback = 1 - self.prob_pos_feedback


class Harry(FeedbackSimulator):
    def __init__(self):
        super(Harry, self).__init__()
        self.set_probabilities()

    def set_probabilities(self):
        self.prob_substantive_feedback = 0.2
        self.prob_bc_feedback = 0.4
        self.prob_no_feedback = 0.4
        self.prob_pos_feedback = 0.7
        self.prob_neg_feedback = 1 - self.prob_pos_feedback


class Neville(FeedbackSimulator):
    def __init__(self):
        super(Neville, self).__init__()
        self.set_probabilities()

    def set_probabilities(self):
        self.prob_substantive_feedback = 0.5
        self.prob_bc_feedback = 0.25
        self.prob_no_feedback = 0.25
        self.prob_pos_feedback = 0.3
        self.prob_neg_feedback = 1 - self.prob_pos_feedback


class LunaAttentiveClever(FeedbackSimulator):
    def __init__(self):
        super(LunaAttentiveClever, self).__init__()
        self.set_probabilities()

    def set_probabilities(self):
        self.prob_substantive_feedback = 0.3
        self.prob_bc_feedback = 0.6
        self.prob_no_feedback = 0.1
        self.prob_pos_feedback = 0.7
        self.prob_neg_feedback = 1 - self.prob_pos_feedback


class LunaInattentiveClever(FeedbackSimulator):
    def __init__(self):
        super(LunaInattentiveClever, self).__init__()
        self.set_probabilities()

    def set_probabilities(self):
        self.prob_substantive_feedback = 0.1
        self.prob_bc_feedback = 0.2
        self.prob_no_feedback = 0.7
        self.prob_pos_feedback = 0.7
        self.prob_neg_feedback = 1 - self.prob_pos_feedback


class LunaAttentiveStupid(FeedbackSimulator):
    def __init__(self):
        super(LunaAttentiveStupid, self).__init__()
        self.set_probabilities()

    def set_probabilities(self):
        self.prob_substantive_feedback = 0.3
        self.prob_bc_feedback = 0.6
        self.prob_no_feedback = 0.1
        self.prob_pos_feedback = 0.3
        self.prob_neg_feedback = 1 - self.prob_pos_feedback


class LunaInattentiveStupid(FeedbackSimulator):
    def __init__(self):
        super(LunaInattentiveStupid, self).__init__()
        self.set_probabilities()

    def set_probabilities(self):
        self.prob_substantive_feedback = 0.1
        self.prob_bc_feedback = 0.2
        self.prob_no_feedback = 0.7
        self.prob_pos_feedback = 0.3
        self.prob_neg_feedback = 1 - self.prob_pos_feedback