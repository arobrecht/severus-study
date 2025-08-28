from typing import Optional, List

import numpy as np
from copy import deepcopy

# MCTS can either have a time limit or a limit of numbers of rollout executions. Per Default the time limit is chosen
# to ensure the runtimes are as specified.
from ..config import TIME_LIMIT, EXPLORATION_CONSTANT, POSSIBLE_ACTION_THRESHOLD, TERMINAL_THRESHOLD, MCTS_TRIPLE_NUM, \
    COMBINABLE_MOVES

from .mcts import mcts
from .triple_action import ActionType, TripleAction
from severusStudy.snape.content.block import Block
from ..partner.partner import Partner


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
    searcher: mcts

    def __init__(
            self,
            block: Block,
            partner: Partner,
            templates: dict,
            combined_templates: dict,
            baseline_order: Optional[list[str]],
            ontology
    ):
        """Create a conditioned explanation state instance for the provided explanation :block.

        Args:
            block: Block instance for which the State is created.
            partner: Reference to the partner model to use.
            templates: A dictionary of the LLM created templates for certain moves. Is not used when using Neo4J!
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
        self.searcher = mcts(timeLimit=TIME_LIMIT, rolloutPolicy=self.limited_random_rollout,
                             explorationConstant=EXPLORATION_CONSTANT)
        self.block_nodes = {}
        self.templates = templates
        self.combined_templates = combined_templates
        # a question is represented with the node id as key and the question type as value
        self.last_question = {}
        # A conditioned_explanation holds its own reward as this is necessary for MCTS
        self.reward = 0
        self.ontology = ontology

    def __repr__(self):
        return "<State = {}, cud = {} grounded_triple = {}>".format(self.block_nodes, self.cud,
                                                                    [node_id for node_id in self.block_nodes if
                                                                     self.get_node_lou(node_id) > TERMINAL_THRESHOLD])

    @property
    def block_name(self):
        return self.block.name

    def reset_searcher(self):
        """Reset the MCTS instance to defaults."""
        self.searcher = mcts(timeLimit=TIME_LIMIT, rolloutPolicy=self.limited_random_rollout,
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
                        "Spielzüge": "Okay, jetzt geht es um die Spielzüge von Quarto.",
                        "Spielziel": "Oh, bisher habe ich noch gar nicht erzählt, was eigentlich das Ziel ist.",
                        "Spieler": "Jetzt noch kurz ein paar Infos zu den Spielern.",
                        "Ende": "Ich erkläre dir jetzt wann Quarto endet.",
                        "Strategien": "Fast geschafft, aber jedes gute Spiel braucht Taktiken."}
        self.at_block_start = False
        print("INTRO", introduction[self.block.name])
        return f"{introduction[self.block.name]}"

    def get_action_info(self, actions: [TripleAction]) -> str:
        move_only = True
        """Return template string for provided :action.
        The string is selected randomly from a list of possible templates for :action.
        Used strings are removed from this list as long as there are other options.
        If all templates have been used, a random sample is chosen.

        Args:
            actions: TripleActions for which a template is selected. Can be one or more.

        Returns:
            Template string for :actions.
        """
        if move_only:
            return str(actions)

        if self.combined_templates == {}:
            nodes = []
            for action in actions:
                nodes.append(self.block_nodes[action.triple_id])

            combined_template = ""

            # check if combined template is available, if yes: return combined template, else: combine manually
            if len(nodes) > 1:
                triple_combined = ""
                for i in range(len(nodes)):
                    if i != len(nodes) - 1:
                        triple_combined += f"{nodes[i].triple.strip()}, "
                    else:
                        triple_combined += f"{nodes[i].triple.strip()}"

                # you only need to get possible templates from one of the triple, because node saved combined templates to each triple equally.
                # hash(''.join(sorted(string))) hashes the triple combination independently of the triple order
                key = hash(''.join(sorted(triple_combined)).strip())
                if key in nodes[0].templates_combined.keys():
                    # TODO: ontology_node != conditioned_node
                    possible_templates = set(nodes[0].templates_combined[key][actions[0].action_type]).difference(
                        self.template_set)

                    if len(possible_templates) < 1:
                        print("WARNING: random template selection")
                        combined_template += self._rng.choice(nodes[0].templates_combined[key][actions[0].action_type])

                    else:
                        print(possible_templates)
                        template = self._rng.choice(list(possible_templates))
                        self.template_set.add(template)
                        combined_template += template

                    return combined_template

            # combine templates manually or just use one template
            for i in range(len(nodes)):
                print(nodes[i].templates)
                possible_templates = set(nodes[i].templates[actions[i].action_type]).difference(
                    self.template_set
                )
                if len(possible_templates) < 1:
                    print("WARNING: random template selection")
                    combined_template += self._rng.choice(nodes[i].templates[actions[i].action_type]) + " "

                else:
                    template = self._rng.choice(list(possible_templates))
                    self.template_set.add(template)
                    combined_template += template + " "

            return combined_template
        else:
            nodes = []
            for action in actions:
                nodes.append(self.block_nodes[action.triple_id])

            combined_template = ""

            # check if combined template is available, if yes: return combined template, else: combine manually
            if len(nodes) == 2:
                triple_combined = [nodes[0].triple + ";" + nodes[1].triple, nodes[1].triple + ";" + nodes[0].triple]
                for key in triple_combined:
                    if key in self.combined_templates.keys():

                        possible_templates = set(self.combined_templates[key][actions[0].action_type]).difference(
                            self.template_set)
                        if len(possible_templates) < 1:
                            print("WARNING: random template selection")
                            combined_template += self._rng.choice(self.combined_templates[key][actions[0].action_type])
                        else:
                            template = self._rng.choice(list(possible_templates))
                            self.template_set.add(template)
                            combined_template += template
                        return combined_template

            # combine templates manually or just use one template
            for i in range(len(nodes)):
                possible_templates = set(self.templates[nodes[i].triple][actions[i].action_type]).difference(
                    self.template_set
                )
                if len(possible_templates) < 1:
                    print("WARNING: random template selection")
                    combined_template += self._rng.choice(self.templates[nodes[i].triple][actions[i].action_type]) + " "

                else:
                    template = self._rng.choice(list(possible_templates))
                    self.template_set.add(template)
                    combined_template += template + " "
            return combined_template

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
        instance = ConditionedExplanationState(self.block, self.partner, baseline_order=self.baseline_order,
                                               templates=self.templates, combined_templates=self.combined_templates, ontology=self.ontology)
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
        for questioned_node in self.last_question.keys():
            if self.last_question[questioned_node] == 0: #open question
                legal_actions.append(TripleAction(ActionType.ANSWER_DECLARATIVE, self.ontology.get_node(questioned_node).triple,
                                                  self.ontology.get_node(questioned_node).id, self.ontology.get_node(questioned_node).block))

            elif self.last_question[questioned_node] == 1: # confirmation question
                for Action in [ActionType.ANSWER_POLAR, ActionType.ANSWER_SUMMARIZE]:
                    legal_actions.append(TripleAction(Action, self.ontology.get_node(questioned_node).triple,
                                                      self.ontology.get_node(questioned_node).id, self.ontology.get_node(questioned_node).block))

            else: # rejection question
                for Action in [ActionType.ANSWER_DECLARATIVE, ActionType.ANSWER_SUMMARIZE]:
                    legal_actions.append(TripleAction(Action, self.ontology.get_node(questioned_node).triple,
                                                      self.ontology.get_node(questioned_node).id, self.ontology.get_node(questioned_node).block))
        if legal_actions:
            return list(set(legal_actions))
        for node in self.block_nodes.values():
            if self.get_node_lou(node.id) == 0:
                legal_actions.append(TripleAction(ActionType.PROVIDE_DECLARATIVE, node.triple, node.id, node.block))
            elif self.get_node_lou(node.id) < POSSIBLE_ACTION_THRESHOLD:
                legal_actions.append(TripleAction(ActionType.DEEPEN_REPEAT, node.triple, node.id, node.block))

                # if example template exists!
                if node.has_example:
                    legal_actions.append(TripleAction(ActionType.DEEPEN_EXAMPLE, node.triple, node.id, node.block))

                # if comparisons exist!
                if node.has_comparison:
                    legal_actions.append(TripleAction(ActionType.DEEPEN_COMPARISON, node.triple, node.id, node.block))
                    legal_actions.append(TripleAction(ActionType.PROVIDE_COMPARISON, node.triple, node.id, node.block))

                legal_actions.append(TripleAction(ActionType.DEEPEN_ADDITIONAL, node.triple, node.id, node.block))
        if all([self.get_node_lou(node_id) > TERMINAL_THRESHOLD for node_id in self.block_nodes.keys()]):
            #legal_actions.append(TripleAction(ActionType.STRUCTURE_SUMMARIZE, "node.triple", -1))
            #legal_actions.append(TripleAction(ActionType.STRUCTURE_COMPREHENSION, "node.triple", -1))
            legal_actions.append(TripleAction(ActionType.STRUCTURE_BRIDGING, "node.triple", -1, "Structure"))
            #legal_actions.append(TripleAction(ActionType.STRUCTURE_MENTALIZE, "node.triple", -1))

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
        next_state.cud = [action]
        if action.action_type in [ActionType.ANSWER_DECLARATIVE, ActionType.ANSWER_SUMMARIZE, ActionType.ANSWER_POLAR]:
            if action.triple_id not in self.block_nodes.keys():
                next_state.cud = self.cud

        if action.triple_id == -1:
            next_state.last_question = {}
            return next_state

        try:
            node = next_state.block_nodes[action.triple_id]
            node_lou = next_state.get_node_lou(node.id)
        except:
            node = self.ontology.get_node(action.triple_id)
            node_lou = node.lou
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
        # deepen+repeat should work better with lower attentiveness
        elif action_type in [ActionType.DEEPEN_REPEAT, ActionType.DEEPEN_ADDITIONAL]:
            return (1+self.partner.attentiveness)/2
            # previously: return self.partner.attentiveness
        elif action_type in [ActionType.DEEPEN_COMPARISON, ActionType.DEEPEN_EXAMPLE]:
            return self.partner.attentiveness
            # previously: return self.partner.attentiveness * self.partner.attentiveness
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
        if action.triple in self.block_nodes.keys():
            prev_lou = self.get_node_lou(action.triple_id)
        else:
            prev_lou = self.ontology.get_node(action.triple_id).lou
        if action.action_type == ActionType.PROVIDE_DECLARATIVE:
            return (1 + (self.partner.expertise * 0.5 / self.block_nodes[action.triple_id].complexity)) / 2
        elif action.action_type == ActionType.PROVIDE_COMPARISON:
            return (1 + (self.partner.expertise * self.partner.expertise / self.block_nodes[action.triple_id].complexity)) / 2
        elif action.action_type in [ActionType.DEEPEN_REPEAT, ActionType.DEEPEN_EXAMPLE]:
            return prev_lou + (self.partner.expertise * 0.5 / self.block_nodes[action.triple_id].complexity)
        elif action.action_type in [ActionType.DEEPEN_COMPARISON, ActionType.DEEPEN_ADDITIONAL]:
            return prev_lou + (
                    self.partner.expertise * self.partner.expertise / self.block_nodes[action.triple_id].complexity)
        elif action.action_type == ActionType.ANSWER_POLAR and action.triple_id in self.last_question.keys():
            return prev_lou + (1 - prev_lou) * (1 - self.partner.cognitive_load)
        elif action.action_type == ActionType.ANSWER_SUMMARIZE and action.triple_id in self.last_question.keys():
            return prev_lou + (1 - prev_lou) * (self.partner.cognitive_load)
        elif action.action_type == ActionType.ANSWER_DECLARATIVE and action.triple_id in self.last_question.keys():
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
        if action.action_type in [ActionType.ANSWER_POLAR, ActionType.ANSWER_SUMMARIZE,
                                  ActionType.ANSWER_DECLARATIVE]:
            if action.triple_id in self.last_question.keys():
                return 100
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
            elif self.check_distance([self.cud[0], action]):
                dist = 1
            else:
                dist = 2
            if self.check_child([self.cud[0], action]):
                child = 0
            else:
                child = 1
        else:
            dist = 0
            child = 0
        if action.action_type in [ActionType.PROVIDE_COMPARISON, ActionType.PROVIDE_DECLARATIVE]:
            if self.get_node_lou(action.triple_id) > 0:
                return -20
            # should depend on block length
            reward = 0
            node_id = action.triple_id
            dependencies = self.block_nodes[node_id].dependencies
            dependency_in_block = [dep["id"] for dep in dependencies if dep["id"] in self.block_nodes.keys()]
            reward = reward - dist
            reward = reward - child*2
            if len(dependency_in_block) > 0:
                for dep in dependency_in_block:
                    reward += self.get_node_lou(dep)
                    reward -= len(dependency_in_block)
                #reward /= len(dependency_in_block)
            #print("Reward",reward, "cud", self.cud, action, "dist", dist, "child", child, "dep", dependency_in_block)
            return reward

        if action.action_type == ActionType.DEEPEN_ADDITIONAL:
            #if dist == 1:
                #print("DISTANCE",dist, "T1:", self.cud[0], "T2:", action)
            return -dist*5
        if action.action_type == ActionType.DEEPEN_COMPARISON:
            return -dist*5
        if action.action_type == ActionType.DEEPEN_REPEAT:
            return -dist*5
        if action.action_type == ActionType.DEEPEN_EXAMPLE:
            return -dist*5


        else:
            return -30

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


        if self.needs_introduction():
            introduction = self.get_introduction()
            return introduction, False, False, [None], []
        mcts_output = (
            None if is_baseline else self.searcher.search(initialState=self, n=MCTS_TRIPLE_NUM, needDetails=True))

        best_actions: List[TripleAction] | TripleAction | None =  mcts_output["action"] if mcts_output else None

        if best_actions is None:
            raise RuntimeError

        def get_best_combination(best_actions: list[TripleAction]) -> list[TripleAction]:
            action1 = best_actions[0]
            if len(best_actions) < 2 or action1.action_type not in COMBINABLE_MOVES:
                return [action1]

            def is_same_type(a, b):
                return a.action_type == b.action_type

            if len(best_actions) >= 3:
                if is_same_type(best_actions[0], best_actions[1]):
                    if is_same_type(best_actions[0], best_actions[2]):
                        if self.check_distance(best_actions[:3]):
                            return best_actions[:3]  # combine all three
                    if self.check_distance([best_actions[0], best_actions[1]]):
                        return best_actions[:2]
                if is_same_type(best_actions[0], best_actions[2]):
                    if self.check_distance([best_actions[0], best_actions[2]]):
                        return [best_actions[0], best_actions[2]]
            if len(best_actions) >= 2 and is_same_type(best_actions[0], best_actions[1]):
                if self.check_distance([best_actions[0], best_actions[1]]):
                    return best_actions[:2]
            return [action1]

        best_actions = get_best_combination(best_actions)

        info = self.get_action_info(best_actions)
        self.cud = best_actions

        return info, True, False, best_actions, deepcopy(mcts_output)

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
        limit = 10
        decay = 0.7
        reward = state.reward
        while step < limit and not state.isTerminal():
            try:
                action = np.random.choice(state.getPossibleActions())
            except IndexError:
                raise Exception("Non-terminal state has no possible actions: " + str(state))
            new_reward = state.get_action_based_reward(action)
            reward += new_reward*(decay**step)
            state = state.takeAction(action)
            step += 1
        return reward

    @staticmethod
    def check_distance(triple_list: list[TripleAction]) -> bool:
        """
        Returns True if each action in the list has at least one other action with a 'distance' < 1.
        """
        if triple_list[0].action_type == 7:
            non_additional_blocks = {a.block for a in triple_list if a.block != "Additional"}
            if len(non_additional_blocks) < 1:
                return False

        triples = [a.triple.split() for a in triple_list]
        for i, a in enumerate(triples):
            has_close_neighbor = False
            for j, b in enumerate(triples):
                if i == j:
                    continue
                if (
                        (a[0] == b[0] and a[1] == b[1]) or
                        (a[1] == b[1] and a[2] == b[2]) or
                        (a[0] == b[0] and a[2] == b[2])
                ):
                    has_close_neighbor = True
                    break
            if not has_close_neighbor:
                return False
        return True

    @staticmethod
    def check_child(triple_list: list[TripleAction]) -> bool:

        # Here we check, if a next triple is a direct child of the cud

        """
        if object of cud is subject of next, output is true
        Args:
             triple_list: list of TripleAction

        Returns:
            True if direct child.
            False if not.
        """

        triples = [a.triple for a in triple_list]

        for i in range(len(triples) - 1):
            a = triples[i]
            b = triples[i + 1]
            a_parts = a.split()
            b_parts = b.split()
            if a_parts[2] == b_parts[0]:
                return True
        return False