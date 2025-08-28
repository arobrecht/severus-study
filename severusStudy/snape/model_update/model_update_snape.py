import random
from pathlib import Path
from pprint import pprint
from typing import Optional, Any
import time

import pandas as pd

from ..config import *
from severusStudy.snape.content.block import Block
from ..content.conditioned_node import ConditionedNode
from ..databank.neo4j_interface import Neo4jInterface
from ..decision_making.conditioned_explanation import ConditionedExplanationState
from ..decision_making.triple_action import TripleAction, ActionType
from ..onotology_management.ontology_management import OntologyManagement
from ..partner.partner import Partner
from ..utils.logger import Logger


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
    partnermodel_logger: Optional[Logger]
    dialog_logger: Optional[Logger]
    run_idx: Optional[int]

    def __init__(
            self,
            partner: Partner,
            partnermodel_logger: Optional[Logger],
            dialog_logger: Optional[Logger],
            run_idx: Optional[int],
            uid,
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

        if USE_POP:
            plan = []
            for blocks in POP_ORDER:
                blocks_shuffled = random.sample(blocks, len(blocks))
                plan += blocks_shuffled
            print(f"Partially Ordered Plan: {plan}")
            self.plan = plan
        else:
            self.plan = [
                "Spiel", "Spielbrett", "Spielfiguren",
                "Spieler", "Spielziel", "Spielzüge",
                "Ende", "Strategien",
            ]

        self.current_idx = 0
        self.saved_idx = 0

        self.baseline_dict = None
        self.is_baseline = is_baseline
        self.partner_update_disabled = disable_partner_update
        self.partner = partner
        self.history = []
        self.feedback = {}
        self.templates = {}
        self.combined_templates = {}
        self.last_best_actions = []
        self.mcts_output = []
        self.is_verification = {'is_verification':False, 'info': None} # indicator for nlu when a feedback value is answer to verification question

        verification_question_data = pd.read_csv(Path(__file__).parent / "../content/verification_questions.csv")
        self.verification_questions = {
            row["block"]: {"answers": [row["answer"].lower()], "question": row["question"], "summary": row["summary"]}
            for _, row in verification_question_data.iterrows()
        }

        self.blocks = {
            row["block"]: Block(id=row["block"], name=row["name"], nodes_ids=[], question=row["question"],
                valid_answers=[row["answer"].lower()])
            for _, row in verification_question_data.iterrows()
        }

        if NEO4J:
            #3 Versuche
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    self.global_state = Neo4jInterface(uri=NEO4J_HOST, admin_login=NEO4J_USER, admin_password=NEO4J_PASSWORD, user_id=str(uid))
                    for block_name in self.blocks.keys():
                        self.blocks[block_name].node_ids = self.global_state.get_block_nodes(block_name)
                    break
                except Exception as e:
                    retry_count += 1
                    print(f"Error connecting to Neo4j (attempt {retry_count}/{max_retries}): {str(e)}")
                    if retry_count >= max_retries:
                        raise  # Re-raise wenn wir mehr als 3 Versuche hatten
                    time.sleep(1)
        block_name = self.get_current_block_id()

        self.current_state = ConditionedExplanationState(
            self.blocks[block_name],
            self.partner,
            baseline_order=None if self.baseline_dict is None else self.baseline_dict[block_name],
            templates=self.templates,
            combined_templates=self.combined_templates,
            ontology=self.global_state
        )
        self.current_state.block_nodes = self.get_block_nodes()
        self.current_state.reward = 0
        self.partnermodel_logger = partnermodel_logger
        self.dialog_logger = dialog_logger
        self.run_idx = run_idx
        if self.partnermodel_logger is not None:
            self.partnermodel_logger.append(
                [
                    str(partner.expertise),
                    str(partner.attentiveness),
                    str(partner.cooperativeness),
                    str(partner.cognitive_load),
                    str(run_idx),
                    str(block_name),
                ]
            )
        self.current_state.reset_searcher()


    def update_knowledge_basis_after_action(self, actions):
        """
        Args:
            actions: the last actions that were taken, as two actions can also be combined.

        Returns:
            The changed lous and improvements, which are however, only necessary for logging as the changes in lou are
            already conducted within this function.
        """

        lous = []
        improvements = []
        for action in actions:
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
            if self.dialog_logger is not None:
                self.dialog_logger.append(
                    [
                        str(self.run_idx),
                        *self.last_best_actions.log,
                        str(improvements),
                    ]
                )
        return lous, improvements

    def update_pm(self):
        self.partner.update(self.feedback)

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
        NEO4J = True
        if NEO4J:
            return self.global_state.get_block_nodes(self.current_state.block.name)
        else:
            return {id: self.global_state.get_node(id) for id in self.current_state.block.node_ids}

    def process_feedback_update_state(self):
        """
        Processes feedback, updates state variables -> preparation for mcts

        If substantial feedback was given, the concerned triples and question types
        are added to the conditioned explanation state as last_question. Also, adjusts
        the lou based on the question type.

        Returns:
            q_type: The type of question inferred from the feedback.
        """

        q_type = None



        # Reset last_question dictionary
        self.current_state.last_question = {}

        if self.feedback:
            subject_feedback = self.feedback.get("sub")
            # Ensure subject feedback is not None or empty
            if subject_feedback:
                q_type = subject_feedback[1]
                triples = subject_feedback[0]
                if q_type not in [-1,-2,-3]:
                    #print("Triple for subject feedback: ", triples)
                    # Iterate over matches
                    for triple in triples:
                        matched_triples = self.global_state.match_triple(triple)
                        print("Triple: ", triple, "Matched: ", matched_triples)
                        question_triple_id = list(matched_triples.keys())[0]
                        print("question triple id: ", question_triple_id)
                        # Save question type for each match
                        self.current_state.last_question[question_triple_id] = q_type

                        # Adjust the level of understanding based on question type for each match
                        lou_adjustment = 0 if q_type == 1 else -LOU_FEEDBACK_ADJUSTMENT

                        node = self.global_state.get_node(question_triple_id)
                        self.global_state.set_lou(question_triple_id, max(0, node.lou + lou_adjustment))
        # Block nodes and reward have to be updated/reset before every MCTS run
        if self.current_state.isTerminal() and q_type != -3:
            self.transition_block()
        self.current_state.block_nodes = self.get_block_nodes()
        self.current_state.reward = 0

        if self.last_best_actions and self.last_best_actions[0].triple_id in self.current_state.block_nodes:
            self.current_state.cud = self.last_best_actions
        else:
            self.current_state.cud = []

        return q_type

    def generate_explanation(self) -> tuple[dict, Any, Any, Any, bool]:
        """
        Generates the next explanation info

        """
        q_type = self.process_feedback_update_state()
        if q_type == -1:
            self.current_state.last_question = {}
            return  {
            'move': "METACOMMUNICATION",
            'triple': "",
            'comparison_triple': "",
            'comparison_domain': "",
            'question_type': -1,
            'utterance': "",
        }, True, False, None, False
        if q_type == -2:
            self.current_state.last_question = {}
            return  {
            'move': "VERIFICATION_ANSWER",
            'triple': "",
            'comparison_triple': "",
            'comparison_domain': "",
            'question_type': -2,
            'utterance': "",
        }, True, False, None, False
        if q_type == -3:
            self.current_state.last_question = {}
            for node_id, node in self.current_state.block_nodes.items():
                self.global_state.set_lou(node_id, node.lou - 0.4)
            return  {
            'move': "VERIFICATION_ANSWER",
            'triple': "",
            'comparison_triple': "",
            'comparison_domain': "",
            'question_type': -3,
            'utterance': "",
        }, True, False, None, False

        # Get last explanation: run MCTS ...
        explanation, feedback_required, is_validation, best_actions, mcts_output = self.current_state.get_explanation(
            is_baseline=self.is_baseline
        )

        # Save mcts output for PM visualization
        self.mcts_output = mcts_output

        # Init explanation info
        move = triple = utterance = comparison_triple_id = comparison_domain = triple_ids = None

        # If one or more actions are found were in the explanation process
        if best_actions[0]:

            # Retrieve top action and accompanying move
            best_action = best_actions[0]
            move = best_action.action_type.name


            # STRUCTURE_BRIDGING is the only possible move at the end of a given block (see legal_actions)
            if move == 'STRUCTURE_BRIDGING':
                question_info = self.verification_questions[self.get_current_block_id()]
                utterance = question_info["question"]
                move = 'VERIFICATION_QUESTION'
                self.is_verification = {'is_verification': True, 'info': question_info}
                feedback_required = False


            # examples require explicit handling
            elif move == 'DEEPEN_EXAMPLE':

                # Retrieve and select a random example from the database
                examples = self.global_state.get_node_examples(best_action.triple_id)
                utterance = random.choice(examples)

            # comparisons require explicit handling
            elif move in ['DEEPEN_COMPARISON', 'PROVIDE_COMPARISON']:

                # get possible comparisons
                comparisons = self.global_state.get_node_comparisons(best_action.triple_id)
                comparison = random.choice(comparisons)

                comparison_triple_id = comparison["triple_id"]
                comparison_domain = 'Chess' if comparison['domain'][0] == 'CHESS_ENTITY' else 'TicTacToe'
                triple = [best_action.triple]
                triple_ids = [best_action.triple_id]

                # Mark the comparison triple as used
                self.global_state.set_node_used_in_comparisons(comparison_triple_id, comparison['domain'][0])



            # if multiple actions were returned, return all triples
            elif len(best_actions) > 1:
                triple = [action.triple for action in best_actions]
                triple_ids = [action.triple_id for action in best_actions]
            else:
                triple = [best_action.triple]
                triple_ids = [best_action.triple_id]

            self.last_best_actions = best_actions
            self.update_knowledge_basis_after_action(best_actions)

        # if no action was returned were in the intro or block transition
        else:
            utterance = explanation

        # dict with all required info for the NLG
        explanation = {
            'move': move,
            'triple': triple,
            'comparison_triple_id': comparison_triple_id,
            'comparison_domain': comparison_domain,
            'question_type': q_type,
            'utterance': utterance,
            'triple_ids': triple_ids,
        }
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

        if feedback["bc"] is not None:
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
                baseline_order=None if self.baseline_dict is None else self.baseline_dict[block_name],
                templates=self.templates,
                combined_templates=self.combined_templates,
                ontology=self.global_state
            )
            self.current_state.block_nodes = self.get_block_nodes()
            self.current_state.reward = 0

        self.flush_log()

    def flush_log(self):
        """Flush the log queues, if not None."""
        if self.dialog_logger is not None:
            self.dialog_logger.flush()

        if self.partnermodel_logger is not None:
            self.partnermodel_logger.flush()
