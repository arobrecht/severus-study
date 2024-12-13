from abc import abstractmethod
from uuid import uuid4
import numpy as np


class PartnerNotFoundException(Exception):
    """Unknown Partner name."""


class Partner:
    """Class to represent an Explainee and it's model properties.

    Attributes:
        expertise: Explainees expertise value
        attentiveness: Explainees attentiveness value
        negative_feedback_prob: Probability for the Explainee to provide negative feedback in a simulation environment.
        positive_feedback_prob: Probability for the Explainee to provide positive feedback in a simulation environment.
        name: Name of the explainee model for logging.
    """

    expertise: float
    attentiveness: float
    cooperativeness: float
    cognitive_load: float
    positive_feedback_prob: float
    negative_feedback_prob: float
    name: str
    _init_expertise: float
    _init_attentiveness: float
    _rng: np.random.Generator

    def __init__(
            self,
            expertise=1,
            attentiveness=1,
            cooperativeness=1,
            cognitive_load=0,
            negative_feedback_prob=0.33,
            positive_feedback_prob=0.33,
            name=str(uuid4()),
    ):
        """Create a new explainee partner instance.

        Args:
            expertise: Expertise value of the model. Defaults to 0.5.
            attentiveness: Attentiveness value of the model. Defaults to 0.5.
            negative_feedback_prob: Probability of giving negative feedback in a simulation. Defaults to 0.33.
            positive_feedback_prob: Probability of giving positive feedback in a simulation. Defaults to 0.33.
            name: Name of the explainee for logging. Defaults to str(uuid4()).
        """
        self._init_expertise = expertise
        self._init_attentiveness = attentiveness
        self._rng = np.random.default_rng()

        self.name = name
        self.expertise = expertise
        self.attentiveness = attentiveness
        self.negative_feedback_prob = negative_feedback_prob
        self.positive_feedback_prob = positive_feedback_prob
        self.cooperativeness = cooperativeness
        self.cognitive_load = cognitive_load

    def __str__(self):
        return f"{self.name}_{self.negative_feedback_prob:0.2g}_{self.positive_feedback_prob:0.2g}".replace(
            "0.", ""
        )

    def reset(self):
        """Reset partner model properties (expertise and attentiveness) to initial values."""
        self.expertise = self._init_expertise
        self.attentiveness = self._init_attentiveness

    @abstractmethod
    def update(self, observations):
        ...

    # the get_feedback function can be used to simulate feedback
    @abstractmethod
    def get_feedback(self) -> str:
        ...
