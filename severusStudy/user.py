#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  6 14:37:20 2017

@author: jpoeppel
"""
import csv
import datetime
import os
import uuid
from pathlib import Path

import pandas as pd

from . import socketio
from . import utils
from .nlg.nlg_lookup import NLG
from .snape.model_update.model_update_snape import ModelUpdate
from severusStudy.nlu.nlu import NLU

from .snape.partner.handle_dbn import DbnPartner
from config import NLU_LLM

# You may want to define experiment/condition handling classes here or elsewhere and
# potentially assign users references to specific instances to handle your experiment flow.


# this has to hold the experimental state I guess...
class User(object):
    def __init__(
        self, remAdr, user_agent, user_number, experiment_type, crowd_user=False
    ):
        self.uid = str(uuid.uuid1())
        attentiveness = (
            0.5 if experiment_type == "initial" else 0.8
        )
        expertise = 0.75
        cooperativeness = 0.75
        cognitive_load = 0.5
        self.partner = DbnPartner(expertise, attentiveness, cooperativeness, cognitive_load)

        disable_partner_update = (
            experiment_type == "baseline" or experiment_type == "initial"
        )

        self.snape = ModelUpdate(
            self.partner,
            None,
            None,
            0,
            self.uid,
            is_baseline= experiment_type == "baseline",
            disable_partner_update=disable_partner_update,
        )

        # required for visualization
        self.utterance_id = 0
        self.pm_data = []

        # used for cognitive load calculation from feedback
        self.delete_count_history = []
        self.mean_character_delay_history = []

        self.nlu = None
        if NLU_LLM:
            self.nlu = NLU()

        self.nlg = NLG()


        self.user_number = user_number
        self.remAdr = remAdr
        self.sid = -1
        self.turn = 0
        self.logActions = True
        self.got_feedback = False
        self.crowd_id = (
            None  # the user's id from the crowd sourcing site, e.g. MTurk ID
        )
        self.finished = False
        self.snape_finished = False
        self.crowd_user = crowd_user

        self.experiment_type = experiment_type
        if experiment_type == "baseline":
            path  = os.path.join(os.path.dirname(os.path.abspath(__file__)), './nlg/baseline_utterances.csv')
            self.baseline_utterances = pd.read_csv(path, delimiter=';')["utterance"].to_list()

        # Log some basic information about the user. Consider if you need to log this
        if user_agent:
            user_agent_info = (
                "User_agent.platform: {}\nUser_agent.browser: {}\n"
                "User_agent.version: {}\nUser_agent.language: {}\n"
                "User_agent.string: {}".format(
                    user_agent.platform,
                    user_agent.browser,
                    user_agent.version,
                    user_agent.language,
                    user_agent.string,
                )
            )
        else:
            user_agent_info = "No info available"
        utils.log(
            self.uid,
            None,
            "Remote address: {}\nUser Agent Information: {}\nUser number: {}\nIs crowd: {}\n".format(
                self.remAdr, user_agent_info, self.user_number, self.crowd_user
            ),
            datetime.datetime.utcnow(),
            self.experiment_type
        )

        if not os.path.exists(Path(f"resultsSeverusStudy/{str(self.uid)}")):
            os.makedirs(f"resultsSeverusStudy/{str(self.uid)}", exist_ok=True)

        with open(Path(f"resultsSeverusStudy/{str(self.uid)}/access_times.csv"), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=";")
            writer.writerow(["timestamp", "route"])



    def get_baseline_utterances(self, utterance_id):
        if len(self.baseline_utterances) -1 == utterance_id:
            self.finished = True
        return self.baseline_utterances[utterance_id]

    def add_crowd_id(self, _id):
        """
        Add the inserted id of the crowd service site (e.g. MTurk) and directly log it
        to the user info.
        """
        self.crowd_id = _id
        utils.log(self.uid, None, "CrowdID: {}".format(_id), datetime.datetime.utcnow())

    def log_user_action(self, action):
        """
        Example function to record and log a user's actions.
        This uses the very simple logging function in the utils.
        """
        utils.log(
            self.uid,
            "TestCondition",
            "User action: {}".format(action),
            datetime.datetime.utcnow(),
        )

    def log_snape_turn(
        self,
        cud_triples: [str | None],
        move: str | None,
        template: str,
        lous: [float | None],
        partner: DbnPartner,
    ):
        utils.log(
            self.uid,
            self.turn,
            "SNAPE",
            str(int(datetime.datetime.now().timestamp() * 1000)),
            self.snape.get_current_block_id(),
            cud_triples,
            #template['utterance'],
            #template['move'],
            lous,
            partner.attentiveness,
            partner.expertise,
            partner.cooperativeness,
            partner.cognitive_load,
            #template['comparison_domain'],
            #template['comparison_triple'],
            #template['question_type']
        )

    def log_question_feedback(self, question: str, word_num: int, answer_found: bool, answer: str, type: str):
        utils.log(self.uid, question, word_num, answer_found, answer, type)

    def log_user_turn(
        self, cud_triple: str | None, feedback: str, lou: float | None, partner: DbnPartner,
            delete_count_history: [int], mean_character_delay_history: [float]
    ):
        utils.log(
            self.uid,
            self.turn,
            "USER",
            str(int(datetime.datetime.now().timestamp() * 1000)),
            self.snape.get_current_block_id(),
            cud_triple,
            feedback,
            lou,
            partner.attentiveness,
            partner.expertise,
            partner.cooperativeness,
            partner.cognitive_load,
            delete_count_history,
            mean_character_delay_history
        )

    @staticmethod
    def log_feedback_exit(uid: str, feedback: str):
        dirPath = f"resultsSeverusStudy/{str(uid)}"
        if not os.path.isdir(dirPath):
            os.makedirs(dirPath)

        with open(f"{dirPath}/feedback", 'a', newline='') as feedbackFile:
            feedbackFile.writelines(feedback)
            feedbackFile.write("\n")

    def log_feedback(self, feedback: str):
        User.log_feedback_exit(self.uid, feedback)

    def log_routing_time(self, route: str):
        with open(f"resultsSeverusStudy/{str(self.uid)}/access_times.csv", 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=";")
            writer.writerow([datetime.datetime.utcnow(), route])

    # Give users their own emit, so that each user gets their own socketio room
    # and messages of different users do not interfere with each other
    def emit(self, event, data):
        socketio.emit(event, data, room=self.sid)

    # region Flask-login functions.
    #
    # Usually not required and currently only setup for a static admin.
    @property
    def is_authenticated(self):
        return self.uid == self.app.config["SECRET_ADMIN_USERNAME"]

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return self.uid != self.app.config["SECRET_ADMIN_USERNAME"]

    def get_id(self):
        return str(self.uid)

