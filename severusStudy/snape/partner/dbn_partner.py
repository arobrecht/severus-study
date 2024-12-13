from severusStudy.snape.partner.partner import Partner
import pyAgrum as gum
from severusStudy.snape.partner.initialize_dbn import initialize_dbn
import pyAgrum.lib.dynamicBN as gdyn


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
        dbn = initialize_dbn()
        self.dbn = gdyn.unroll2TBN(dbn, 1000)
        self.ie = gum.LazyPropagation(self.dbn)
        self.index = 1

    def update(self, observations):
        # the evidence is set to have no feedback included and is than updated with the feedback.
        # This is passed through the DBN which updates the partner attributes
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
        self.ie.updateEvidence(evidence)
        self.attentiveness = calc_expected_value(self.ie.posterior(f"a_{self.index}"))
        self.expertise = calc_expected_value(self.ie.posterior(f"e_{self.index}"))
        self.cooperativeness = calc_expected_value(self.ie.posterior(f"c_{self.index}"))
        self.cognitive_load = calc_expected_value(self.ie.posterior(f"l_{self.index}"))
        '''
        print("Attentiveness: ", self.attentiveness)
        print("Expertise: ",self.expertise)
        print("Cooperativeness: ",self.cooperativeness)
        print("Cognitive Load: ",self.cognitive_load)
        '''
        self.index += 1


if __name__ == "__main__":
    dbn = DbnPartner(1, 1, 1, 1)
    print("attentivness:", dbn.attentiveness, " expertise:", dbn.expertise, " cooperativeness:", dbn.cooperativeness,
          " cognitive_load:", dbn.cognitive_load)
    for i in range(4):
        observations = {"feedback": False, "bc": None, "sub": None, "validation_answer": None}
        dbn.update(observations)
        print("attentivness:", dbn.attentiveness, " expertise:", dbn.expertise, " cooperativeness:",
              dbn.cooperativeness, " cognitive_load:", dbn.cognitive_load)
