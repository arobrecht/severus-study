import pandas as pd

from severusStudy import Manager
from severusStudy.snape.partner.feedback_generator import Hermine, Neville, Draco, Harry, Ron, LunaAttentiveStupid, LunaInattentiveStupid, LunaAttentiveClever, LunaInattentiveClever


def run_study_simulation(feedback_generator_list, file_name):
    feedback_gen_index = 0
    switch_index = 30

    columns = ['utterance_id', 'block',
               'cooperativeness',
               'cognitive_load',
               'attentiveness',
               'expertise', 'selected_move', 'selected_triple', 'sub_feedback', 'tae', 'bc_feedback']

    # Initialize the CSV file by writing headers
    df = pd.DataFrame(columns=columns)
    df.to_csv(file_name, index=False)
    utterance_id = 1

    manager = Manager()
    user = manager.new_user(None, None, "adaptive")

    # We apply it to times before the loop as we want the introduction and no feedback on the introduction. In the study
    # this is not possible and therefore we don't want to make it possible here
    explanation, feedback_required, is_validation, actions, partner_update_disabled = user.snape.generate_explanation()
    print(explanation)
    while not user.snape.is_finished():
        explanation, feedback_required, is_validation, actions, partner_update_disabled = user.snape.generate_explanation()
        print(explanation)
        feedback = feedback_generator_list[feedback_gen_index].get_feedback(user.snape.last_best_actions[0])
        print(feedback)
        user.snape.process_user_feedback(feedback)
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
                # Convert new_data to a DataFrame
                new_df = pd.DataFrame(new_data)

                # Append new data to the CSV file
                new_df.to_csv(file_name, mode='a', header=False, index=False)
                utterance_id += 1

        if utterance_id % switch_index == 0 and len(feedback_generator_list) != 1:
            feedback_gen_index += 1
            feedback_gen_index = feedback_gen_index % len(feedback_generator_list)


def study_simulation_runner(characters, pm, runs=50):
    for iteration in range(runs):
        for character, run in characters.items():
            if run:
                file_name = f'./{pm}/{character}/simulation_results_{pm}{character}{iteration}.csv'
                if character == 'Luna':
                    feedback_simulator_list = [ LunaAttentiveClever(), LunaAttentiveStupid(), LunaInattentiveStupid(), LunaInattentiveClever()
]
                else:
                    feedback_simulator_list = [globals()[character]()]
                run_study_simulation(feedback_simulator_list, file_name)


if __name__ == "__main__":
    # number of iterations for each character
    iterations = 140

    # only used for filename -> change model by importing different pm in conditioned_explanation
    model = 'initialize_dbn'

    # control which characters should be simulated
    character_control = {
        'Hermine': True,
        'Neville': True,
        'Harry': True,
        'Ron': True,
        'Luna': True
    }
    study_simulation_runner(characters=character_control, pm=model, runs=iterations)