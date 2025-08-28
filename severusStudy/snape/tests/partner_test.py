from ..partner.handle_dbn import DbnPartner
from ..partner.feedback_generator import Hermine
from ..decision_making.triple_action import ActionType, TripleAction
from ..config import CARRY_OVER, DBN_MAX_SIZE


def calc_expected_outcome(feedback_to_verify, variable):
    if variable == "pos":
        if feedback_to_verify["bc"] == "+":
            return 1
        else:
            return 0
    return None


def test_carry_over():
    # First we populate the DBN and check that the lower positions are filled while the last position is not yet.
    # After, we create a spillover and check that the first 10 (1+9) are populated and the number 11 (1+10) is not.
    # Different tests are not possible as I am not able to access the actual feedback given, so I cannot check whether the feedback is correct carried over.
    partner = DbnPartner(1, 1, 1, 1)
    feedback_generator = Hermine()
    last_action = TripleAction(ActionType.PROVIDE_DECLARATIVE, "Ein test triple", 2, "block")
    feedback = [feedback_generator.get_feedback(last_action) for _ in range(3)]
    partner.ie.setEvidence({"pos_1": 'yes'})
    start_evidence_pos = list(partner.ie.hardEvidenceNodes())[0]
    print("all Evidences", partner.ie.hardEvidenceNodes())
    partner.ie.setEvidence({"neg_1": 'yes'})
    start_evidence_neg = list(partner.ie.hardEvidenceNodes())[0]
    partner.ie.setEvidence({"sub_1": 'yes'})
    start_evidence_sub = list(partner.ie.hardEvidenceNodes())[0]
    partner.ie.eraseAllEvidence()
    for single_feedback in feedback:
        partner.update(single_feedback)
    feedback = [feedback_generator.get_feedback(last_action) for _ in range(15)]
    for single_feedback in feedback:
        partner.update(single_feedback)
    assert partner.ie.hasEvidence(start_evidence_pos + 7) == True
    assert partner.ie.hasEvidence(start_evidence_pos + 18) == False
    assert partner.ie.hasEvidence(start_evidence_neg + 7) == True
    assert partner.ie.hasEvidence(start_evidence_neg + 18) == False
    assert partner.ie.hasEvidence(start_evidence_sub + 7) == True
    assert partner.ie.hasEvidence(start_evidence_sub + 18) == False
    feedback = [feedback_generator.get_feedback(last_action) for _ in range(DBN_MAX_SIZE- 15 -3)]
    for single_feedback in feedback:
        partner.update(single_feedback)
    assert partner.ie.hasEvidence(start_evidence_pos + (CARRY_OVER -1) ) == True
    assert partner.ie.hasEvidence(start_evidence_pos + CARRY_OVER) == False
    assert partner.ie.hasEvidence(start_evidence_neg + (CARRY_OVER -1)) == True
    assert partner.ie.hasEvidence(start_evidence_neg + CARRY_OVER) == False
    assert partner.ie.hasEvidence(start_evidence_sub + (CARRY_OVER -1)) == True
    assert partner.ie.hasEvidence(start_evidence_sub + CARRY_OVER) == False
