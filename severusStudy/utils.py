#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilities for logging results of studies. 
This uses a thread-safe queue object
@author: jpoeppel
"""

import queue

log_queue = queue.Queue()


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
