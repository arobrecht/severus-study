import unittest

from ..content.block import Block
from ..content.conditioned_node import ConditionedNode
from severusStudy.snape.onotology_management.global_state import GlobalState
from ..partner.partner import Partner
from .conditioned_explanation import ConditionedExplanationState


class TestConditionedExp(unittest.TestCase):

    precondition_node: ConditionedNode
    state: ConditionedExplanationState

    def setUp(self):
        self.precondition_node = ConditionedNode(
            block="block1",
            triple="is(QUARTO, BOARDGAME)",
            dependencies=[],
            complexity=1,
        )
        node = ConditionedNode(
            block="block1",
            triple="has(QUARTO, BOARD)",
            dependencies=[self.precondition_node.id],
            complexity=2,
        )
        global_state = GlobalState(nodes=[node, self.precondition_node])
        block = Block(
            "block1",
            "block1",
            nodes_ids=[self.precondition_node.id, node.id],
            question="",
            valid_answers=[],
        )
        partner = Partner.getRon()

        self.state = ConditionedExplanationState(
            global_state=global_state, block=block, partner=partner, baseline_order=None
        )

    def test_getReward_nothing_grounded(self):
        reward = self.state.getReward()
        self.assertAlmostEqual(reward, -2.0)

    def test_getReward_precondition(self):
        self.state.global_state.nodes[self.precondition_node.id].lou = 0.4
        reward = self.state.getReward()
        self.assertAlmostEqual(reward, -1.6)

    def test_getReward_precondition_grounded(self):
        self.state.global_state.nodes[self.precondition_node.id].lou = 0.8
        reward = self.state.getReward()
        self.assertAlmostEqual(reward, -0.2)


if __name__ == "__main__":
    unittest.main()
