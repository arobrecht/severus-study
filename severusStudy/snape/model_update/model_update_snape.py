from abc import abstractmethod
from pathlib import Path
from typing import Optional, Union

from severusStudy.snape.content.block import Block
from severusStudy.snape.content.conditioned_node import ConditionedNode
from severusStudy.snape.content.quarto_ontology import parse_ontology
from severusStudy.snape.databank.neo4j_interface import Neo4jInterface
from severusStudy.snape.onotology_management.ontology_management import OntologyManagement
from severusStudy.snape.partner.partner import Partner
from severusStudy.snape.solver.conditioned_explanation import ConditionedExplanationState
from severusStudy.snape.solver.triple_action import TripleAction


class ModelUpdate:
    """SNAPE explainer model.

    Attributes:
        current_state: ConditionedExplanationState instance for the current block.
        last_best_actions: The latest best actions as determined by MCTS. Can be multiple or one action(s).
        history: List of provided user feedback.
        blocks: Dictionary of block instances, keyed by block name.
        is_baseline: Bool indicating if baseline mode is activated.
        partner_update_disabled: Bool indicating if the partner properties update is disabled.
        baseline_dict: Dictionary containing a list of triples to provide for each block, keyed by block name.
        partner: The partner model instance for the explainee.
        global_state: GlobalStateof the explanation.
        partnermodel_logger: Logger instance for partner related logging.
        dialog_logger: Logger instance for dialog related logging.
        run_idx: Index of the current run, if simulating.

    """

    current_state: ConditionedExplanationState
    last_best_actions: [TripleAction]
    history: list[tuple[[TripleAction], int]]
    blocks: dict[str, Block]
    is_baseline: bool
    partner_update_disabled: bool
    baseline_dict: Optional[dict[str, list[str]]]
    partner: Partner
    global_state: OntologyManagement
    run_idx: Optional[int]

    def __init__(
            self,
            partner: Partner,
            run_idx: Optional[int],
            is_baseline=False,
            disable_partner_update=False,
    ):
        """Create a SNAPE explainer instance.
        Parses the ontology, creates a global state, a state instance for the first block and initializes the MCTS algorithm.

        Args:
            partner: The partner model instance for the explainee.
            partnermodel_logger: Logger instance for partner related logging.
            dialog_logger: Logger instance for dialog related logging.
            run_idx: Index of the current run, if simulating.
            baseline: Bool indicating if baseline mode is activated. Defaults to False.
            disable_partner_update: Bool indicating if the partner properties update is disabled. Defaults to False.

        """
        self.plan = [
            "Spiel",
            "Spielbrett",
            "Spielfiguren",
            "Spieler",
            "Spielzuege",
            "Spielziel",
            "Ende",
            "Strategien",
        ]

        self.current_idx = 0
        self.saved_idx = 0

        self.is_baseline = is_baseline
        self.partner_update_disabled = disable_partner_update
        self.partner = partner
        self.history = []
        self.feedback = {}
        self.last_best_actions = []

        content_dir = Path(__file__).parent / ".." / "content" / "ontologies"

        self.blocks, nodes, self.baseline_dict, additional_information = parse_ontology(
            f'{content_dir / "new_ontology.csv"}',
            f'{content_dir / "verification_questions.csv"}',
            f'{content_dir / "templates_llm.csv"}')
        neo4j_uri = "bolt://localhost:7687"
        neo4j_login = "neo4j"
        neo4j_password = "severus_study"
        self.global_state = Neo4jInterface(uri=neo4j_uri, login=neo4j_login, password=neo4j_password)
        for block_name in self.blocks.keys():
            self.blocks[block_name].node_ids = self.global_state.get_block_nodes(block_name)
        block_name = self.get_current_block_id()
        self.current_state = ConditionedExplanationState(
            self.blocks[block_name],
            self.partner,
            baseline_order=None if self.baseline_dict is None else self.baseline_dict[block_name])
        self.current_state.block_nodes = self.get_block_nodes()
        self.current_state.reward = 0
        self.run_idx = run_idx
        self.current_state.reset_searcher()

    @abstractmethod
    def update_knowledge_basis_after_action(self, actions):
        ...

    @abstractmethod
    def update_pm(self):
        ...

    def get_current_block_id(self) -> str:
        """Get the block name of the currently active block.

        Returns:
            Block name (id) as string.
        """
        if self.current_idx < len(self.plan):
            return self.plan[self.current_idx]
        else:
            return "Finished"

    def is_finished(self):
        """Returns true when the plan is executed.
        Returns:
            True if finished, false otherwise
        """
        return self.current_idx >= len(self.plan)

    def get_saved_block_id(self) -> str:
        """
        Gets the block name from the saved block
        Returns:
            Block name (id) as string.
        """
        return self.plan[self.saved_idx]

    def reset_to_saved_block(self):
        self.current_idx = self.saved_idx

    def reset(self):
        """Reset global state. Set index to zero"""
        self.current_idx = 0

    def get_block_nodes(self) -> dict[int, ConditionedNode]:
        """Return list of nodes in global state contained in current block.

        Returns:
            List of ConditionedNode instances.
        """
        return self.global_state.get_block_nodes(self.current_state.block.name)

    def generate_explanation(
            self,
    ) -> tuple[str, bool, bool, [Union[None, TripleAction]], bool]:
        """Generate the next explanation string for the dialog.
        If a new block is started, it is introduced.
        If the block is grounded, a validation question is returned.
        If :baseline is True, the next provide action is returned.
        Otherwise, the next best action within the block is determined using MCTS.

        Raises:
            RuntimeError: Raised if MCTS could not find a possible action.

        Returns:
            A tuple containing the explanation string, a bool telling if feedback is
            required, a bool indicating whether the returned value is a validation question, the action
            if available and another bool indicating whether the partner update is disabled.
        """

        # if substantial feedback was given the concerned triples and the question types are added to the conditioned
        # explanation state as last_question
        if self.current_state.isTerminal():
            self.transition_block()
        self.current_state.last_question = {}
        if self.feedback != {}:
            if self.feedback["sub"] is not None:
                questions, question_type = self.global_state.match_triple(self.feedback["sub"][1])
                if question_type != 0:
                    for question in questions:
                        self.current_state.last_question[question] = question_type
                        if question_type == 2:
                            self.global_state.set_lou(question, self.global_state.get_node(question).lou + 0.2)
                        else:
                            self.global_state.set_lou(question, max(0, self.global_state.get_node(question).lou - 0.2))

        # Block nodes and reward have to be updated/reset before every MCTS run
        self.current_state.block_nodes = self.get_block_nodes()
        self.current_state.reward = 0
        if len(self.last_best_actions) > 0 and self.last_best_actions[0].triple_id in self.current_state.block_nodes:
            self.current_state.cud = self.last_best_actions
        else:
            self.current_state.cud = []
        explanation, feedback_required, is_validation, best_actions = self.current_state.get_explanation(
            is_baseline=self.is_baseline)
        # We ensure that at least one valid action was returned
        if best_actions[0] is not None:
            self.last_best_actions = best_actions
            self.update_knowledge_basis_after_action(best_actions)
        return explanation, feedback_required, is_validation, best_actions, self.partner_update_disabled

    def process_user_feedback(
            self, feedback: dict
    ) -> tuple[Optional[bool], Optional[str]]:
        """Process the users response given by :feedback.
        If the current state is terminal, the feedback is processed as an answer to a validation question.
        Otherwise, node lous that the question refers to are update, the partner model is updated and the feedback
        is added to the feedback history

        Args:
            feedback: User feedback as a dict with the keys: feedback, bc, sub, validation_answer
        Returns:
            Tuple of bool and string if the current state is terminal. Tuple of None otherwise.
        """

        if self.is_baseline:
            print("WARNING: overwriting baseline feedback")
            feedback["bc"] = "+"

        elif feedback["bc"] is not None:
            if feedback["bc"] == "+":
                for action in self.last_best_actions:
                    self.global_state.set_lou(action.triple_id, 0.9)
            else:
                # smiley hinzufügen damit neg überhaupt existiert
                for action in self.last_best_actions:
                    self.global_state.set_lou(action.triple_id, 0.4)
        self.feedback = feedback
        self.history.append(
            (
                self.last_best_actions,
                0
                if feedback["bc"] is None and feedback["sub"] is None
                else 1
                if feedback["bc"] == "+"
                else -1,
            )
        )
        if not self.partner_update_disabled:
            self.update_pm()
        return None, None

    def transition_block(self):
        """Create a state instance for the next block in the global plan and update the partner
        model properties, if not disabled.
        """
        self.current_state.reset_searcher()
        self.current_idx = min(self.current_idx + 1, len(self.plan))

        if not self.is_finished():
            block_name = self.get_current_block_id()
            self.current_state = ConditionedExplanationState(
                self.blocks[block_name],
                self.partner,
                baseline_order=None if self.baseline_dict is None else self.baseline_dict[block_name]
            )
            self.current_state.block_nodes = self.get_block_nodes()
            self.current_state.reward = 0
