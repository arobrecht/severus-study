import pandas as pd
from config import VISUALIZATION
#from config import NLG_LLM
from severusStudy import Manager
from severusStudy.snape.partner.pm_visualization import create_visualization
from severusStudy.snape.partner.feedback_generator import Hermine, Neville, Draco, Harry, Ron, LunaAttentive, LunaInattentive, Realistic, Demo
from severusStudy.nlg.nlg_lookup import NLG

def run_study_simulation(feedback_generator_list, file_name, fail_file_name):

    # list to hold data to pass to visualization
    pm_data = []
    feedback_gen_index = 0
    switch_index = 30

    columns = ['utterance_id', 'block',
               'cooperativeness',
               'cognitive_load',
               'attentiveness',
               'expertise', 'selected_move', 'selected_triple', 'sub_feedback', 'tae', 'bc_feedback']
    columns_fail = ['utterance', "action"]
    df_fail = pd.DataFrame(columns=columns_fail)
    df_fail.to_csv(fail_file_name, index=False)

    # Initialize the CSV file by writing headers
    df = pd.DataFrame(columns=columns)
    df.to_csv(file_name, index=False)
    utterance_id = 1

    manager = Manager()
    user = manager.new_user(None, None, "adaptive")
    nlg = NLG()

    # We apply it to times before the loop as we want the introduction and no feedback on the introduction. In the study
    # this is not possible, and therefore we don't want to make it possible here
    explanation, feedback_required, is_validation, actions, partner_update_disabled = user.snape.generate_explanation()
    print(f"{explanation}\n")

    if VISUALIZATION:
        create_visualization(block=user.snape.current_state.block.name,
                             pm_data=pm_data,
                             actions=user.snape.mcts_output,
                             last_action='INTRO',
                             last_feedback=user.snape.feedback,
                             utterance=explanation['utterance'])

    while not user.snape.is_finished():

        explanation, feedback_required, is_validation, actions, partner_update_disabled = user.snape.generate_explanation()
        feedback = feedback_generator_list[feedback_gen_index].get_feedback(user.snape.last_best_actions[0])
        user.snape.process_user_feedback(feedback)

        # log data
        if len(actions) > 0:
            for action in actions:
                new_data = {
                    'utterance_id': [utterance_id],
                    'block': [user.snape.current_state.block.name],
                    'cooperativeness': [user.snape.partner.cooperativeness],
                    'cognitive_load': [user.snape.partner.cognitive_load],
                    'attentiveness': [user.snape.partner.attentiveness],
                    'expertise': [user.snape.partner.expertise],
                    'selected_move': [action.action_type if action is not None else ""],
                    'selected_triple': [action.triple if action is not None else ""],
                    'sub_feedback': [feedback["sub"]],
                    'tae': [feedback["tae"]] if "tae" in feedback.keys() else 'no',
                    'bc_feedback': [feedback["bc"]],
                }
                pm_data.append(new_data)
                # Convert new_data to a DataFrame
                new_df = pd.DataFrame(new_data)

                # Append new data to the CSV file
                new_df.to_csv(file_name, mode='a', header=False, index=False)
                utterance_id += 1

        # switch feedback generators
        if utterance_id % switch_index == 0 and len(feedback_generator_list) != 1:
            feedback_gen_index += 1
            feedback_gen_index = feedback_gen_index % len(feedback_generator_list)

        # generate utterance
        action_str, utterance = nlg.process_explanation_nlg(explanation, True)
        utterance_data = {'utterance': utterance, 'action': action_str}
        new_fail_data = pd.DataFrame(utterance_data, index=[0])
        new_fail_data.to_csv(fail_file_name, mode='a', header=False, index=False)

        """
        if VISUALIZATION:
            create_visualization(block=user.snape.current_state.block.name,
                                 pm_data=pm_data,
                                 actions=user.snape.mcts_output,
                                 last_action=action_str,
                                 last_feedback=user.snape.feedback,
                                 utterance=utterance)
        """
        #print(f"action: {actions}\nfeedback: {feedback}")
        print(f"action: {actions}\nfeedback: {feedback}\ngenerated utterance: {utterance}")


def study_simulation_runner(characters, pm, runs=5):
    for iteration in range(runs):
        for character, run in characters.items():
            if run:
                file_name = f'study_simulation_results/{pm}/{character}/simulation_results_{pm}_{character}_{iteration}.csv'
                fail_file_name = f'study_simulation_results/{pm}/{character}/utterances_simulation_results_{pm}_{character}_{iteration}.csv'
                if character == 'Luna':
                    feedback_simulator_list = [LunaAttentive(), LunaInattentive()]
                else:
                    feedback_simulator_list = [globals()[character]()]
                run_study_simulation(feedback_simulator_list, file_name, fail_file_name)


if __name__ == "__main__":
    # number of iterations for each character
    iterations = 10

    # only used for filename -> change model by importing different pm in dbn_partner
    model = 'dbn_realistic'

    # control which characters should be simulated
    character_control = {
        'Hermine': False,
        'Neville': False,
        'Draco': False,
        'Harry': False,
        'Ron': False,
        'Luna': False,
        'Realistic': False,
        'Demo': True,
    }

    study_simulation_runner(characters=character_control, pm=model, runs=iterations)