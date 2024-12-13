from copy import deepcopy
from typing import Optional, List

import numpy as np

from .mcts import mcts_modified
from .triple_action import ActionType, TripleAction
from ..content.block import Block
from ..partner.partner import Partner

# required LOU of a node to be considered as grounded
TERMINAL_THRESHOLD = 0.75

# minimum initial lou
INIT_LOU = 0.0

# maximum LOU for actions (except PROVIDE) to be selected for search in mcts
POSSIBLE_ACTION_THRESHOLD = 0.8

# MCTS can either have a time limit or a limit of numbers of rollout executions.
TIME_LIMIT = 3000
SEARCH_LIMIT = 300
EXPLORATION_CONSTANT = 1


class ConditionedExplanationState:
    """Class to represent a conditioned state parsed from an ontology.
    Implements interface for MCTS library. See [mcts repository](https://github.com/pbsinclair42/MCTS/blob/master/exampleInterfaces.py) for reference.
    Node properties for the state are taken from the global state reference attribute. If the state modifies the
    lou for a specific node, it is kept in the temporary override dict :lou_overrides until the action is performed (performAction).

    Attributes:
        partner: Reference to the partner model.
        lou_overrides: Dict to override the lou for triple identifiers (key).
        block: Block of the current state
        template_set: maps action type to (<state factor>, <transition prob. factor>).
        baseline_order: List of triple identifiers for baseline mode.
        at_block_start: Bool indicating if the state was newly created.
        cud: List of Triples currently under discussion
        searcher: mcts searcher.
    """

    partner: Partner
    lou_overrides: dict[int, float]
    block: Block
    template_set: set
    baseline_order: Optional[list[str]]
    at_block_start: bool
    cud: list
    searcher: mcts_modified

    def __init__(
            self,
            block: Block,
            partner: Partner,
            baseline_order: Optional[list[str]],
    ):
        """Create a conditioned explanation state instance for the provided explanation :block.

        Args:
            block: Block instance for which the State is created.
            partner: Reference to the partner model to use.
            baseline_order: Optional list of triple identifiers for baseline mode.

        """
        self.template_set = set()
        self.lou_overrides = {}
        self.partner = partner
        self.cud = []
        self.block = block
        self.baseline_order = baseline_order
        self._rng = np.random.default_rng()
        self.at_block_start = True
        self.searcher = mcts_modified(timeLimit=TIME_LIMIT, rolloutPolicy=self.limited_random_rollout,
                             explorationConstant=EXPLORATION_CONSTANT)
        self.block_nodes = {}
        # a question is represented with the node id as key and the question type as value
        self.last_question = {}
        # A conditioned_explanation holds its own reward as this is necessary for MCTS
        self.reward = 0

    def __repr__(self):
        return "<State = {}, cud = {} grounded_triple = {}>".format(self.block_nodes, self.cud,
                                                                    [node_id for node_id in self.block_nodes if
                                                                     self.get_node_lou(node_id) > TERMINAL_THRESHOLD])

    @property
    def block_name(self):
        return self.block.name

    def reset_searcher(self):
        """Reset the MCTS instance to defaults."""
        self.searcher = mcts_modified(timeLimit=TIME_LIMIT, rolloutPolicy=self.limited_random_rollout,
                             explorationConstant=EXPLORATION_CONSTANT)

    def needs_introduction(self) -> bool:
        """Blocks newly started require an introduction to the user."""
        return self.at_block_start

    def get_introduction(self) -> str:
        """Returns a simple introduction sentence containing the block name.

        Returns:
            Introduction string.
        """
        introduction = {"Spiel": "Hallo, heute erkläre ich dir das Spiel Quarto.",
                        "Spielfiguren": "Als nächstes möchte ich dir etwas über die Spielfiguren erzählen.",
                        "Spielbrett": "Lass uns mit dem Spielbrett weitermachen.",
                        "Spielzuege": "Okay, jetzt geht es um die Spielzüge von Quarto.",
                        "Spielziel": "Oh, bisher habe ich noch gar nicht erzählt, was eigentlich das Ziel ist.",
                        "Spieler": "Jetzt noch kurz ein paar Infos zu den Spielern.",
                        "Ende": "Aber wann ist Quarto überhaupt vorbei?",
                        "Strategien": "Fast geschafft, aber jedes gute Spiel braucht Taktiken."}
        self.at_block_start = False
        print("INTRO", introduction[self.block.name])
        return f"{introduction[self.block.name]}"

    # function name can not be adapted to convention as mcts needs this method to exist
    def getCurrentPlayer(self):
        """Return mcts player identifier (1 or -1).

        Returns:
            1 constant
        """
        return 1

    def get_node_lou(self, node_id: int) -> float:
        """Get the nodes lou either from the current override or from the global state.

        Args:
            node_id: Id hash of the node.

        Returns:
            The lou for the node with id :node_id, if available.
        """
        if node_id in self.lou_overrides.keys():
            return self.lou_overrides[node_id]
        return self.block_nodes[node_id].lou

    # function name can not be adapted to convention as mcts needs this method to exist
    def isTerminal(self):
        """Flag indicating whether the state is terminal (e.g. grounded).
        A state is considered terminal, if all contained node lou's are
        above the terminal threshold level and the last move was a structuring move.

        Returns:
            Boolean flag inidcating wether the state is terminal.
        """

        if len(self.cud) == 0:
            return False
        if self.cud[0].action_type in [ActionType.STRUCTURE_BRIDGING, ActionType.STRUCTURE_SUMMARIZE,
                                       ActionType.STRUCTURE_MENTALIZE, ActionType.STRUCTURE_COMPREHENSION]:
            if all([(self.get_node_lou(id) > TERMINAL_THRESHOLD) for id in self.block.node_ids]):
                return True
            else:
                return False
        else:
            return False

    def deepcopy(self):
        """Copy state instance.
        Pythons deepcopy does not work on classes.
        I learned this the hard way :(
        """
        instance = ConditionedExplanationState(self.block, self.partner, baseline_order=self.baseline_order)
        instance.at_block_start = self.at_block_start
        instance.lou_overrides = deepcopy(self.lou_overrides)
        instance.cud = deepcopy(self.cud)
        instance.template_set = deepcopy(self.template_set)
        instance.block_nodes = deepcopy(self.block_nodes)
        instance.last_question = deepcopy(self.last_question)
        instance.reward = deepcopy(self.reward)

        return instance

    # From here onwards all relevant changes belonging to the MPD take place

    # function name can not be adapted to convention as mcts needs this method to exist
    def getPossibleActions(self):
        """Get all possible Actions for the current state.
        For not presented nodes, only the PROVIDE actions are possible.
        For all presented but not grounded triples the DEEPEN actions are possible.
        If a question was asked the ANSWER actions only to the referred nodes are possible.
        If all triples are grounded, the STRUCTURE moves are possible. For these the node id is set to -1 to ensure it
        is not considered as an action to a specific node.
        If the state is terminal, an empty list is returned.

        Returns:
            List of possible TripleActions. Empty list for terminal state.
        """
        if self.isTerminal():
            return []

        legal_actions = []

        for node in self.block_nodes.values():
            if self.get_node_lou(node.id) == 0:
                legal_actions.append(TripleAction(ActionType.PROVIDE_COMPARISON, node.triple, node.id))
                legal_actions.append(TripleAction(ActionType.PROVIDE_DECLARATIVE, node.triple, node.id))
            elif self.get_node_lou(node.id) < POSSIBLE_ACTION_THRESHOLD:
                legal_actions.append(TripleAction(ActionType.DEEPEN_REPEAT, node.triple, node.id))
                legal_actions.append(TripleAction(ActionType.DEEPEN_EXAMPLE, node.triple, node.id))
                legal_actions.append(TripleAction(ActionType.DEEPEN_COMPARISON, node.triple, node.id))
                legal_actions.append(TripleAction(ActionType.DEEPEN_ADDITIONAL, node.triple, node.id))
        if all([self.get_node_lou(node_id) > TERMINAL_THRESHOLD for node_id in self.block_nodes.keys()]):
            legal_actions.append(TripleAction(ActionType.STRUCTURE_SUMMARIZE, " node.triple", -1))
            legal_actions.append(TripleAction(ActionType.STRUCTURE_COMPREHENSION, "node.triple", -1))
            legal_actions.append(TripleAction(ActionType.STRUCTURE_BRIDGING, "node.triple", -1))
            legal_actions.append(TripleAction(ActionType.STRUCTURE_MENTALIZE, "node.triple", -1))
        for questioned_node in self.last_question.keys():
            if questioned_node in self.block_nodes.keys():
                for Action in [ActionType.ANSWER_POLAR, ActionType.ANSWER_DECLARATIVE, ActionType.ANSWER_SUMMARIZE]:
                    legal_actions.append(TripleAction(Action, self.block_nodes[questioned_node].triple,
                                                      self.block_nodes[questioned_node].id))

        return list(set(legal_actions))

    # function name can not be adapted to convention as mcts needs this method to exist
    def takeAction(self, action: TripleAction):
        """Apply the provided action to a copied instance of the current state and return it.
        The new lou depends on the action type, the partner model attributes and the nodes complexity.
        All  actions are applied in a probabilistic manner.
        It needs to be worked with the lou overrides as MCTS needs this format and functions to only give a state etc.
        Therefore, it is not possible to go back into the model update and change all that.
        Additionally, the rewards are also calculated in here and assigned to the conditioned node as this will be passed
        further down in MCTS. In the rollout function the reward will be calculated
        """

        next_state = self.deepcopy()
        # the reward is caluclated based on the old state and assigned to the copied reward.
        reward = self.get_action_based_reward(action)
        next_state.reward = reward

        if action.triple_id == -1:
            next_state.last_question = {}
            next_state.cud = [action]
            return next_state
        node = next_state.block_nodes[action.triple_id]
        node_lou = next_state.get_node_lou(node.id)
        # state_factor, transition_prob_factor = TRANSITION_FACTOR_MAP[action.action_type]
        # Here should be the update for the transition probabilities from the paper for th MDP
        next_lou = next_state.calc_next_lou(action)
        transition_prob = next_state.calculate_transition_probability(action)
        next_state.lou_overrides[node.id] = np.random.choice(
            [node_lou, next_lou], p=[1 - transition_prob, transition_prob]
        )
        next_state.last_question = {}
        next_state.cud = [action]
        return next_state

    def calculate_transition_probability(self, action):
        """

        Args:
            action: The action that was chosen

        Returns:
            float representing the transition probability of an action, i.e. the prob of success for that action
        """
        action_type = action.action_type
        if action_type in [ActionType.PROVIDE_COMPARISON, ActionType.PROVIDE_DECLARATIVE,
                           ActionType.STRUCTURE_COMPREHENSION, ActionType.STRUCTURE_BRIDGING,
                           ActionType.STRUCTURE_MENTALIZE, ActionType.STRUCTURE_SUMMARIZE]:
            return 1
        elif action_type in [ActionType.DEEPEN_REPEAT, ActionType.DEEPEN_ADDITIONAL]:
            return self.partner.attentiveness
        elif action_type in [ActionType.DEEPEN_COMPARISON, ActionType.DEEPEN_EXAMPLE]:
            # this is pretty low in my opinion.
            return self.partner.attentiveness * self.partner.attentiveness
            # potentiell: (1+attentivness) /2
        elif action_type in [ActionType.ANSWER_POLAR, ActionType.ANSWER_DECLARATIVE, ActionType.ANSWER_SUMMARIZE]:
            if action.triple_id in self.last_question.keys():
                return 1
            else:
                return 0
        else:
            return 0

    def calc_next_lou(self, action):
        """
        This function calculates the lou of the node the action refers to if the action is successful.
        Args:
            action: The action that is to be performed

        Returns:
            a float that represents the new lou of the node
        """
        prev_lou = self.get_node_lou(action.triple_id)
        if action.action_type == ActionType.PROVIDE_DECLARATIVE:
            return (1 + (self.partner.expertise * 0.5 / self.block_nodes[action.triple_id].complexity)) / 2
        elif action.action_type == ActionType.PROVIDE_COMPARISON:
            return (1 + (self.partner.expertise * self.partner.expertise / self.block_nodes[action.triple_id].complexity)) / 2
        elif action.action_type in [ActionType.DEEPEN_REPEAT, ActionType.DEEPEN_EXAMPLE]:
            return prev_lou + (self.partner.expertise * 0.5 / self.block_nodes[action.triple_id].complexity)
        elif action.action_type in [ActionType.DEEPEN_COMPARISON, ActionType.DEEPEN_ADDITIONAL]:
            return prev_lou + (
                    self.partner.expertise * self.partner.expertise / self.block_nodes[action.triple_id].complexity)
        elif action.action_type == ActionType.ANSWER_POLAR and action.triple_id in self.last_question.keys() and \
                (self.last_question[action.triple_id] == 2 or self.last_question[action.triple_id] == 3):
            return prev_lou + (1 - prev_lou) * (1 - self.partner.cognitive_load)
        elif action.action_type == ActionType.ANSWER_SUMMARIZE and action.triple_id in self.last_question.keys() and \
                (self.last_question[action.triple_id] == 2 or self.last_question[action.triple_id] == 3):
            return prev_lou + (1 - prev_lou) * (self.partner.cognitive_load)
        elif action.action_type == ActionType.ANSWER_DECLARATIVE and action.triple_id in self.last_question.keys() and \
                self.last_question[action.triple_id] == 1:
            return prev_lou + (1 - prev_lou) * 0.5
        else:
            return prev_lou

    def get_action_based_reward(self, action):
        """

        Args:
            action: The action for which the reward is to be calculated

        Returns:
            A float representing the reward of the action depending on the explanation state and partner
        """
        if action.action_type in [ActionType.PROVIDE_COMPARISON, ActionType.PROVIDE_DECLARATIVE]:
            if self.get_node_lou(action.triple_id) > 0:
                return -10
            reward = 0
            node_id = action.triple_id
            dependencies = self.block_nodes[node_id].dependencies
            dependency_in_block = [dep["id"] for dep in dependencies if dep["id"] in self.block_nodes.keys()]

            if len(dependency_in_block) > 0:
                for dep in dependency_in_block:
                    reward -= self.get_node_lou(dep)
                reward /= len(dependency_in_block)
                reward -= 1
            return reward

        if action.action_type in [ActionType.ANSWER_POLAR, ActionType.ANSWER_SUMMARIZE,
                                  ActionType.ANSWER_DECLARATIVE]:
            if action.triple_id in self.last_question.keys():
                return 10
            else:
                return -100
        n_grounded_triples = len(
            [node_id for node_id in self.block_nodes.keys() if self.get_node_lou(node_id) > TERMINAL_THRESHOLD])
        n_of_triple_in_block = len(self.block_nodes.keys())
        if action.action_type == ActionType.STRUCTURE_SUMMARIZE:
            return (n_grounded_triples - n_of_triple_in_block) * 10 + 1 - self.partner.attentiveness
        if action.action_type == ActionType.STRUCTURE_BRIDGING:
            return ((n_grounded_triples - n_of_triple_in_block) * 10 + 1 -
                    self.partner.cognitive_load + self.partner.cooperativeness)
        if action.action_type == ActionType.STRUCTURE_COMPREHENSION:
            return (n_grounded_triples - n_of_triple_in_block) * 10 + 1 - self.partner.cooperativeness
        if action.action_type == ActionType.STRUCTURE_MENTALIZE:
            return (n_grounded_triples - n_of_triple_in_block) * 10 + self.partner.cognitive_load
        if len(self.cud) > 0:
            if self.cud[0].triple_id == action.triple_id:
                dist = 0
            elif self.one_triple_distance([self.cud[0], action]):
                dist = 1
            else:
                dist = 2
        else:
            dist = 0
        if action.action_type == ActionType.DEEPEN_ADDITIONAL:
            return -dist
        if action.action_type == ActionType.DEEPEN_COMPARISON:
            return -dist
        if action.action_type == ActionType.DEEPEN_REPEAT:
            return -dist
        if action.action_type == ActionType.DEEPEN_EXAMPLE:
            return -dist
        else:
            return -10

    def reset(self):
        """Reset state as if it has not been seen yet."""
        self.cud = []
        self.at_block_start = True
        self.template_set = set()

    def get_explanation(self, is_baseline=False):
        """

        Args:
            is_baseline: Whether only the baseline should be considered

        Returns: explanation, feedback_required, is_validation, best_actions

        """
        amount_triples = 2
        if self.needs_introduction():
            introduction = self.get_introduction()
            return introduction, False, False, [None]
        mcts_output = (
            None if is_baseline else self.searcher.search(initialState=self, n=amount_triples, needDetails=True))
        best_actions: List[TripleAction] | TripleAction | None = mcts_output["action"]
        if best_actions is None:
            raise RuntimeError
        # If the best two actions are of the same action type and share at least one entity, they can be explained
        # together
        if not (len(best_actions) > 1 and best_actions[0].action_type == best_actions[1].action_type and
                self.one_triple_distance(best_actions)):
            best_actions = [best_actions[0]]
        info = str(best_actions)
        self.cud = best_actions
        return info, True, False, best_actions

    # https://www.moderndescartes.com/essays/deep_dive_mcts/
    # http://www.diego-perez.net/papers/GECCO_RollingHorizonEvolution.pdf
    # https://arxiv.org/pdf/2103.04931.pdf
    # ideas:
    # simulate outcomes while waiting for feedback!
    # if in doubt, repeat REPEAT, ADDITIONAL action (with different template ofc)

    @staticmethod
    def limited_random_rollout(state, limit: int = 50):

        """Custom rollout function for mcts.
        Enables to limit the simulated random rollout depth for :state by varying :limit.

        Args:
            state: State to be simulated on.
            limit: Depth limit for the simulation. Defaults to 50.

        Raises:
            Exception: Raised if state is invalid.

        Returns:
            Reward of the state at the end of the rollout (reaching depth :limit or terminal state).
        """
        step = 0
        limit = 20
        reward = state.reward
        while step < limit and not state.isTerminal():
            try:
                action = np.random.choice(state.getPossibleActions())
            except IndexError:
                raise Exception("Non-terminal state has no possible actions: " + str(state))
            new_reward = state.get_action_based_reward(action)
            reward += new_reward
            state = state.takeAction(action)
            step += 1
        return reward

    @staticmethod
    def one_triple_distance(triple_list: list[TripleAction]) -> bool:

        # Here we can also compute the distance without the graph! If either the object or the subject is present in
        # both possible actions, the triple distance is below 1 and accepted

        """
        Checks if the triple distance between one and min. one other triple is 1. Returns true if yes, else false.
        Args:
            triple_list: list of TripleAction

        Returns:
            True if all triples have at least one other triple in the list with distance one.
            False if not.
        """
        # create list to store if seen combination has distance one
        distance_is_one = [False] * len(triple_list)

        # check combinations
        for i in range(len(triple_list)):
            if triple_list[i].action_type in [ActionType.STRUCTURE_COMPREHENSION, ActionType.STRUCTURE_BRIDGING,
                                              ActionType.STRUCTURE_SUMMARIZE, ActionType.STRUCTURE_MENTALIZE]:
                continue
            for j in range(len(triple_list)):
                if triple_list[j].action_type in [ActionType.STRUCTURE_COMPREHENSION, ActionType.STRUCTURE_BRIDGING,
                                                  ActionType.STRUCTURE_SUMMARIZE, ActionType.STRUCTURE_MENTALIZE]:
                    continue

                # get first
                first_triple = triple_list[i].triple
                # get second
                second_triple = triple_list[j].triple

                if first_triple != second_triple:
                    # check distance
                    for inst in [first_triple.split(",")[0].replace("(", ""),
                                 first_triple.split(" ")[2].lstrip().replace(")", "")]:
                        if inst in [second_triple.split(" ")[0].replace("(", ""),
                                    second_triple.split(" ")[2].lstrip().replace(")", "")]:
                            # store True for the combination
                            distance_is_one[i] = True
                            distance_is_one[j] = True
                            break

        if all(distance_is_one):
            return True
        else:
            return False
