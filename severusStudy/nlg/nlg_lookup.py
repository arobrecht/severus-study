import json

import pandas as pd
import os

from sympy import Integer


class NLG:
    def __init__(self):

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utterances.json'), 'r', encoding='utf-8') as f:
            self.utterances = json.load(f)


    def _look_up_utterance(self, move, triple_ids, comparison_triple_id='/', comparison_domain='/', answer_type='/'):
        for utterance_id, utterance_info in self.utterances.items():
            if utterance_info['move'] != move:
                continue

            if set(triple_ids) != set(utterance_info['triples']):
                continue

            if (move == 'GENERATE_COMPARISON' and (comparison_triple_id != utterance_info['comparison_triple_id'] or
                comparison_domain != utterance_info['comparison_domain'])):
                    continue

            if move == 'CONFIRM_CLARIFY' and utterance_info['answer_type'] != answer_type:
                continue

            return utterance_info['utterance']


        print(f"NO UTTERANCE FOUND FOR:\n"
              f"move={move}\n"
              f"triple_ids={triple_ids}\n"
              f"comp_triple_id={comparison_triple_id}\n"
              f"comp_domain={comparison_domain}\n"
              f"answer_type={answer_type}")
        return "NO UTTEANCE FOUND"



    def process_explanation_nlg(self,explanation):

        if not explanation.get("move"):
            return 'BLOCK INTRO', explanation["utterance"]

        move = explanation["move"]


        if move == 'FINISHED':
            action_str = 'FINISHED'
            utterance = 'Jetzt sind wir fertig!'

        elif move == 'VERIFICATION_QUESTION':
            action_str = 'VERIFYING BLOCK'
            utterance = explanation["utterance"]

        elif move == "METACOMMUNICATION":
            utterance = "Leider habe ich deine Frage nicht verstanden. Ich kann nur Fragen zu Quarto beantworten. "
            action_str = f"{move}, {utterance}"

        elif move == "VERIFICATION_ANSWER":
            if explanation["question_type"] == -2:
                utterance = "Super, die Antwort war richtig."
                action_str = f"{move}, {utterance}"
            else:
                utterance = "Leider war die Antwort nicht richtig."
                action_str = f"{move}, {utterance}"

        elif move in {"DEEPEN_COMPARISON", "PROVIDE_COMPARISON"}:
            action_str = (
                f"{move} {explanation['triple']}, "
                f"domain: {explanation['comparison_domain']}, triple: {explanation['comparison_triple_id']}"
            )

            utterance = self._look_up_utterance(
                move="GENERATE_COMPARISON",
                triple_ids=explanation["triple_ids"],
                comparison_triple_id=explanation["comparison_triple_id"],
                comparison_domain=explanation["comparison_domain"],
            )

        elif move in {"STRUCTURE_SUMMARIZE", "STRUCTURE_BRIDGING", "STRUCTURE_COMPREHENSION", "STRUCTURE_MENTALIZE"}:
            action_str = move
            utterance = 'Machen wir jetzt mit einem anderen Thema weiter.'

        elif move == "DEEPEN_EXAMPLE":
            action_str = f"{move} {explanation['utterance']}"
            utterance = explanation["utterance"]

        elif move in {"PROVIDE_DECLARATIVE", "DEEPEN_ADDITIONAL", "ANSWER_DECLARATIVE"}:
            action_str = f"{move} {explanation['triple']}"
            utterance = self._look_up_utterance(move="STATE_INFORMATION", triple_ids=explanation["triple_ids"])

        elif move == "DEEPEN_REPEAT":
            action_str = f"{move} {explanation['triple']}"
            utterance = self._look_up_utterance(move=move, triple_ids=explanation["triple_ids"])

        elif move == "ANSWER_SUMMARIZE":
            action_str = f"{move} {explanation['triple']}"
            utterance = self._look_up_utterance(move="CONFIRM_CLARIFY", triple_ids=explanation["triple_ids"],
                                                answer_type=explanation["question_type"])

        else: # polar answer
            action_str = f"{move} [{explanation['question_type']}], {explanation['triple']}"
            # TODO: properly handle question types
            utterance = "Ja!" if explanation["question_type"] == 1 else "Nein!"

        return action_str, utterance
