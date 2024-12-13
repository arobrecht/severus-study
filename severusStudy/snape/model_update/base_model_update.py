from severusStudy.snape.model_update.model_update_snape import ModelUpdate
from severusStudy.snape.solver.triple_action import ActionType


class BaseModelUpdate(ModelUpdate):
    def update_knowledge_basis_after_action(self, last_actions):
        """

        Args:
            last_actions: the last actions that were taken, as two actions can also be combined.

        Returns:
            The changed lous and improvements, which are however, only necessary for logging as the changes in lou are
            already conducted within this function.
        """

        lous = []
        improvements = []
        for action in last_actions:
            if action is None:
                break
            self.current_state.at_block_start = False
            if action.action_type in [ActionType.STRUCTURE_BRIDGING, ActionType.STRUCTURE_MENTALIZE,
                                      ActionType.STRUCTURE_SUMMARIZE, ActionType.STRUCTURE_COMPREHENSION]:
                break
            node_id = action.triple_id
            old_lou = self.global_state.get_node(node_id).lou or 0
            if self.current_state.isTerminal():
                return old_lou, 0
            self.current_state.takeAction(action)
            for overwritten_id, lou in self.current_state.takeAction(action).lou_overrides.items():
                self.global_state.set_lou(overwritten_id, lou)
                # This needs to be removed if this function is kicked out
                self.global_state.set_node_was_seen(overwritten_id)
            lou = self.global_state.get_node(node_id).lou
            lous.append(lou)
            improvements.append(lou - old_lou)

        return lous, improvements

    def update_pm(self):
        self.partner.update(self.feedback)
