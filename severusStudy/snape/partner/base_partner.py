import numpy as np

from severusStudy.snape.partner.partner import Partner


class BasePartner(Partner):
    @staticmethod
    def activation(x):
        """Scale the input :x to the range [0, 1], equivalent to (0.5 + tanh(2*x) / 2)."""
        exponential = np.exp(4 * x)
        return exponential / (1 + exponential)

    def update(self, observations):
        print("BasePartner is deprecated and should not be used anymore. Please use the DbnPartner")
        """Update the partner model properties according to the given feedback.
                Note: Wenn der nutzer negatives FB auf eine simple Aussage generiert, dann sollte das den expertise-Wert stärker schwächen also bei einer schweren Aussage.

                Args:
                    observations: the oberservations that are relevant for the BaseNet
                """
        # TODO: introduce some kind of sensitivity property which adjust the likelihood to change the partners attributes.
        positive_score = 0
        negative_score = 0
        n_not_none = 0

        for element in observations:
            if element[0] == "-":
                negative_score += 4 - element[1]
                n_not_none += 1
            elif element[0] == "+":
                positive_score += element[1]
                n_not_none += 1

        total = positive_score + negative_score

        if total > 0:
            self.expertise = self.expertise * (1 / n_not_none) + self.activation(
                (positive_score - negative_score) / total
            ) * (1 - 1 / n_not_none)

        self.attentiveness = (self.attentiveness + n_not_none / len(observations)) / 2

    def get_feedback(self) -> str:
        """Simulate a probabilistic possible feedback for the current Partner model.

            Returns:
                Feedback string. One of ['+', '-', None]
            """

        return self._rng.choice(
            ["-", "+", "None"],
            p=[
                self.negative_feedback_prob,
                self.positive_feedback_prob,
                1 - (self.positive_feedback_prob + self.negative_feedback_prob),],)
