from ..config import DBN_MAX_SIZE, CARRY_OVER
from ..partner.feedback_generator import Neville
from ..partner.partner import Partner
from ..partner.dbn.dbn_realistic import initialize_dbn
import pyAgrum as gum
import pyAgrum.lib.dynamicBN as gdyn

from ..decision_making.triple_action import ActionType, TripleAction


def calc_expected_value(potential):
    potential_sum = 0
    factor = 0
    for i in range(3):
        potential_sum += potential[i] * factor
        factor += 0.5
    return potential_sum


# The initial values for the partner are chosen in the user.py can, however, be overwritten in this file
class DbnPartner(Partner):
    def __init__(self, expertise, attentiveness, cooperativeness, cognitive_load):
        super(DbnPartner, self).__init__(expertise, attentiveness, cooperativeness, cognitive_load)
        self.max_size = DBN_MAX_SIZE
        self.carry_over = CARRY_OVER
        dbn = self.initialize_new_dbn()
        self.ie = gum.LazyPropagation(dbn)
        self.index = 1
        self.all_evidences = []

    def initialize_new_dbn(self, size=None):
        """Initialize a new DBN with a specified size."""
        size = size if size else self.max_size
        dbn = initialize_dbn()  # Your function to define the base DBN structure
        return gdyn.unroll2TBN(dbn, size)

    def carry_over_states(self):
        """Carry over the last `carry_over` states into a new DBN."""
        new_dbn = self.initialize_new_dbn()
        new_ie = gum.LazyPropagation(new_dbn)
        offset = self.max_size - self.carry_over - 1
        for i in range(0, self.carry_over):
            evidence = {f"pos_{i}": self.all_evidences[i + offset][0], f"neg_{i}": self.all_evidences[i + offset][1],
                        f"sub_{i}": self.all_evidences[i + offset][2],
                        f"tae_{i}": self.all_evidences[i + offset][3]}
            new_ie.updateEvidence(evidence)

        self.dbn = new_dbn
        self.ie = new_ie
        self.index = self.carry_over  # Reset index to account for carry-over
        evs = self.all_evidences[offset:]
        self.all_evidences = []
        for ev in evs:
            self.all_evidences.append(ev)

    def update(self, observations):
        """Update the DBN with new observations."""
        # Reset and carry over if maximum size is reached

        if self.index > self.max_size - 1:
            self.carry_over_states()

        # Define evidence for current timestep
        evidence = {f"pos_{self.index}": 'no', f"neg_{self.index}": 'no', f"sub_{self.index}": 'no',
                    f"tae_{self.index}": 'None'}

        if observations["bc"] is not None:
            if observations["bc"] == "+":
                evidence[f"pos_{self.index}"] = "yes"
            else:
                evidence[f"neg_{self.index}"] = "yes"
        elif observations["sub"] is not None:
            evidence[f"sub_{self.index}"] = "yes"
            evidence[f"tae_{self.index}"] = observations["tae"]

        # Update the DBN evidence
        self.ie.updateEvidence(evidence)
        # Update partner attributes
        self.expertise = calc_expected_value(self.ie.posterior(f"e_{self.index}"))
        self.attentiveness = calc_expected_value(self.ie.posterior(f"a_{self.index}"))
        self.cooperativeness = calc_expected_value(self.ie.posterior(f"c_{self.index}"))
        self.cognitive_load = calc_expected_value(self.ie.posterior(f"l_{self.index}"))
        self.all_evidences.append(list(evidence.values()))

        # print("attentivness:", self.attentiveness, "expertise:", self.expertise, "cooperativeness:", self.cooperativeness, "cognitive_load:", self.cognitive_load)

        # Increment index for the next timestep
        self.index += 1


if __name__ == "__main__":
    feedback_sim = Neville()
    last_action = TripleAction(ActionType.DEEPEN_ADDITIONAL, "haus bauen schnecke", 2)
    dbn = DbnPartner(1, 1, 1, 1)
    for i in range(20):
        feedback = feedback_sim.get_feedback(last_action=last_action)
        observations = feedback
        print(feedback)
        dbn.update(observations)
        print("attentivness:", dbn.attentiveness, "expertise:", dbn.expertise, "cooperativeness:", dbn.cooperativeness,
              "cognitive_load:", dbn.cognitive_load)
