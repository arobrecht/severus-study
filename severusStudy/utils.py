#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilities for logging results of studies. 
This uses a thread-safe queue object
@author: jpoeppel
"""

import os
import queue
import threading
import time
import urllib.request


log_queue = queue.Queue()

# Create the prefix for the result path. This is located on the same level
# as the exampleStudy folder and is called "results"+ <name of 
# the app folder> (exampleStudy in this example)
study_name = os.path.split(os.path.dirname(os.path.realpath(__file__)))[1]
study_name = study_name[0].capitalize() + study_name[1:]
PREFIX = "results" + study_name

def write_log():
    """
        Checks if a new item is in the log_queue und writes the contents 
        into appropriate files. How and where the logs should be written
        should be configured to your needs.

        This very simple examples creates a folder for each user (named according to their
        uid) and creates files for the different conditions to log the user's
        condition responses line by line. 
        If no condition is given, the contents are assumed to belong to general user 
        information.

        A smarter way would be to log in a format that is easily formatable, but you
        should make sure to write to a file as quickly as possible to prevent data loss
        in case the Python process dies unexpectedly.
    """
    while True:
        item = log_queue.get()
        if item is None:
            time.sleep(0.1)
            continue

        content: str = ""
        user_id: str = ""
        filename: str = "general"

        print("item to log: ", item)
        if "feedback" in str(item):
            user_id, question, word_num, answer_found, answer, *rest = item
            content = ";".join([str(x) for x in item[1:5]])
            filename = "feedback"
        elif len(item) > 5:
            user_id, turn, role, timestamp, block, cud, *rest = item
            content = ";".join([str(x) for x in item[1:]])
            filename = "dialogue"
        else:
            user_id, *rest = item
            content = ";".join([str(x) for x in rest])
                    
        prefix = PREFIX
        dirPath = prefix + os.path.sep + str(user_id)

        if not os.path.isdir(dirPath):
            os.makedirs(dirPath)

        with open(dirPath + os.path.sep + filename, "a", encoding="utf-8") as f:
            f.write(f"{content}\n")


logThread = threading.Thread(target=write_log)
logThread.daemon = True
logThread.start()


def log(user_id, *args):
    """
    Add multiple elements into the logging queue. What elements you use
    should depend on your usecase. The write_log function above
    assumes the tuple to always contain a user_id (since it uses the id) to
    setup the folder structure for the logfiles as well as a condition
    identifier, a msg and a timestamp.
    """
    item = [user_id]
    item.extend(args)
    log_queue.put(tuple(item))


def notify_sona_server(user, sona_server_url_template):
    """
    Example function that can be used to communicate with the sona system.
    Potential templates may look like
    """

    def _threaded_notify():
        feedback = urllib.request.urlopen(
            sona_server_url_template.format(user.sonaID)
        ).read()
        user.add_sona_feedback(feedback)

    t = threading.Thread(target=_threaded_notify())
    t.setDaemon(True)
    t.start()


class Logger(object):
    """
    A very naive logging wrapper that allows one to test parts of the
    application also outside the flask context by then simply printing directly.
    Could also be improved by falling back to the standard logging functionality
    of Python.
    """

    def __init__(self):
        self.app = None
        self.silent = False

    def set_app(self, app):
        self.app = app

    def dummy_print(self, text):
        if not self.silent:
            print(text)

    def __getattr__(self, name):
        if self.app:
            return self.app.logger.__getattribute__(name)
        else:
            return self.dummy_print
