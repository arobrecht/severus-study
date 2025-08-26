import traceback

from severusStudy.snape.decision_making.triple_action import TripleAction
from .. import socketio, manager, logger

from config import VISUALIZATION
#from ..nlg.ollama_nlg import nlg
from severusStudy.snape.partner.pm_visualization import create_visualization
import re
from datetime import datetime
from flask import session
import numpy as np

def preprocess_feedback(feedback: str, nlu, is_verification):
    """

    Args:
        feedback: The feedback given by the user
        nlu: The NLU object that was initialized beforehand. If no NLU is used this will be None.

    Returns: the dictionary with the feedback extracted from the input string

    """
    print("Feedback given:", feedback)
    if feedback in ["+", "-"]:
        return {"feedback": True, "bc": feedback, "sub": None}
    elif feedback in ["None", None]:
        return {"feedback": False, "bc": None, "sub": None}
    else:
        print(nlu)
        if nlu is not None:
            triples, question_type = nlu.nlu_pass_olama(feedback, is_verification)
            #reformatted_question = " ".join([entity.strip() for entity in triples.split(",")])
            return {"feedback": True, "bc": None, "sub": [triples, question_type], "tae": "None"}
        else:

            return {"feedback": True, "bc": None, "sub": ["Keine relevante Frage", -2], "tae": "None"}

@socketio.on('disconnect')
def handle_disconnect_event():
    # ... (existing code) ...
    if "uid" in session: # Added to original snippet
        user_uid = session["uid"]
        user = manager.get_user(user_uid)
        if not user:
            logger.error(f"User {user_uid} not found on disconnect.")
            return
        user.snape.global_state.close()
        logger.info(f"User {user_uid} disconnected, closing application related resources.")
    else:
        #logger.info(f"A client with session ID (sid) {request.sid} disconnected, no 'uid' in session.") This can crash
        logger.info(f"A client disconnected, no 'uid' in session.")
    return None


@socketio.on('get_explanation')
def handle_get_explanation():
    try:
        user = manager.get_user(session["uid"])
        if not user:
            logger.error("User not found while getting explanation, returning")
            return False

        if user.snape.is_finished():
            user.snape_finished = True
            manager.save_user(user)
            return None

        if user.experiment_type == "baseline":
            if user.snape_finished:
                print("returned none")
                return None

            baseline_return = handle_get_explanation_baseline()
            print(baseline_return)
            print(user.snape_finished == True)
            return baseline_return

        explanation, feedback_required, is_validation, actions, partner_update_disabled = user.snape.generate_explanation() # handle examples
        if actions:
            is_tripleaction = isinstance(actions[0], TripleAction)
        else:
            is_tripleaction = False

        lous = []
        if is_tripleaction:
            user.utterance_id += 1
            triples = []
            action_type = []
            for action in actions:
                partner_data = {
                    'utterance_id': user.utterance_id,
                    'cooperativeness': [user.snape.partner.cooperativeness],
                    'cognitive_load': [user.snape.partner.cognitive_load],
                    'attentiveness': [user.snape.partner.attentiveness],
                    'expertise': [user.snape.partner.expertise],
                }
                user.pm_data.append(partner_data)
                triples.append(action.triple)
                action_type.append(str(action.action_type))

                if action.triple_id != -1:
                    lous.append(user.snape.global_state.get_node(action.triple_id).lou)
        else:
            triples = [None]
            action_type = None
            lous.append(None)
        logger.debug(triples)

        if feedback_required or is_validation:
            user.turn += 1

        user.log_snape_turn(triples, action_type, explanation, lous, user.snape.partner)
        logger.debug(f"[{user.get_id()}] explanation: {explanation}")

        block = user.snape.current_state.block.name

        if explanation['move'] in ["STRUCTURE_SUMMARIZE", "STRUCTURE_BRIDGING", "STRUCTURE_COMPREHENSION", "STRUCTURE_MENTALIZE"]:
            if user.snape.current_idx == len(user.snape.plan) - 1:
                explanation['move'] = 'FINISHED'
                user.snape.current_idx = len(user.snape.plan)

        action_str, utterance = user.nlg.process_explanation_nlg(explanation)

        if VISUALIZATION:
            create_visualization(block=user.snape.current_state.block.name,
                                pm_data=user.pm_data,
                                actions=user.snape.mcts_output,
                                last_action= action_str,
                                last_feedback=user.snape.feedback,
                                utterance=utterance,
                                user_id=user.uid )

        return utterance, block, feedback_required, is_validation, triples, partner_update_disabled, is_tripleaction
    except Exception as e:
        print(traceback.format_exc())
        logger.error(f"Error in handle_get_explanation: {str(e)}")
        # Return a simple explanation that will trigger the frontend to request another one
        return "Es gab ein Problem bei der Erklärungsgenerierung. Lass uns weitermachen.", None, False, False, None, False, False

def handle_get_explanation_baseline():
    user = manager.get_user(session["uid"])
    if not user:
        logger.error("User not found while getting explanation, returning")
        return False

    if user.finished:
        user.snape_finished = True
        manager.save_user(user)
        return "Jetzt sind wir fertig", None, False, False, None, True, False

    utterance = user.get_baseline_utterances(user.utterance_id)
    user.utterance_id += 1
    return utterance, None, False, False, None, True, False

@socketio.on('feedback')
def handle_feedback(feedback: str) -> str | None:
    try:
        user = manager.get_user(session["uid"])
        if not user:
            logger.error("User not found while handling feedback, returning")
            return None
        if user.experiment_type == "baseline":
            return None
        # sub feedback given
        tae_update = None
        if feedback not in ['None', '+', '-']:
            feedback_chars = re.findall(r"char: '([^']+)'", feedback)
            timestamps = re.findall(r"time: (\S+)", feedback)
            timestamps = [timestamp.strip(',') for timestamp in timestamps]

            times = [datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ") for timestamp in timestamps]
            time_differences = [(times[i + 1] - times[i]).total_seconds() for i in range(len(times) - 1)]

            user.mean_character_delay_history.append(np.mean(time_differences))

            if user.mean_character_delay_history[:-1]:
                previous_avg_time = np.mean(user.mean_character_delay_history[:-1])
                new_avg_time = np.mean(user.mean_character_delay_history)
                tae_update = 'lower' if previous_avg_time > new_avg_time else 'higher'

            user.delete_count_history.append(feedback.count('DELETE'))
            actual_feedback = []
            for char in feedback_chars:
                if char == 'DELETE':
                    if actual_feedback:
                        actual_feedback.pop()
                else:
                    actual_feedback.append(char)
            feedback = ''.join(actual_feedback)
            print("feedback: " + feedback)

        nlu = user.nlu
        feedback_dict = preprocess_feedback(feedback, nlu, user.snape.is_verification)
        user.snape.is_verification = {'is_verification':False, 'info': None}


        if tae_update:
             feedback_dict['tae'] = tae_update

        _, answer = user.snape.process_user_feedback(feedback_dict)
        actions = user.snape.last_best_actions

        if actions:
            is_tripleaction = isinstance(actions[0], TripleAction)
        else:
            is_tripleaction = False
        lous = []
        triples = []
        if is_tripleaction:
            for action in actions:
                if action.triple_id != -1:
                    lous.append(user.snape.global_state.get_node(action.triple_id).lou)
                    triples.append(action.triple)
        else:
            lous.append(None)
            triples.append(None)

        user.log_user_turn(triples, feedback, lous, user.partner,
                        user.delete_count_history, user.mean_character_delay_history)
        # user.log_user_action(f"feedback: {feedback}, answer: {answer}")
        logger.debug(f"[{user.get_id()}] feedback: {feedback}, answer: {answer}")

        return answer
    except Exception as e:
        logger.error(f"Error in handle_feedback: {str(e)}")
        # Return a response that will trigger the frontend to continue
        return "Es gab ein Problem bei der Verarbeitung deines Feedbacks. Lass uns weitermachen."