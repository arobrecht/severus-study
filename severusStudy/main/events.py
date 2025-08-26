from .. import socketio, manager, logger
from . import main
from flask import session, request

import json
    
@socketio.on('responses')
def handle_responses(responses):
    logger.debug("Received responses: {}".format(responses))    
    user = manager.get_user(session["uid"])
    if not user:
        logger.error("User not found while handling ratings, returning")
        return False
    
    user.log_user_action(responses)

    # You can use the return value to decide if you need to load the next
    # questions or do something else.
    return user.finished


@socketio.on('request_questions')
def on_request_questions():
    logger.debug("Front end requested questions")
    questions = []
    questions.append({
        "id": "Thoughts",
        "type": "text",
        "question": "What do you think about this template"
    })
    questions.append({
        "id": "Usage",
        "type": "radio",
        "question": "Would you use this template?",
        "options": ["Yes", "No"]
    })
    return questions

@socketio.on('connect')
def connect():
    try:
        logger.info("User: {} connected from {} (requestId: {})".format(session["uid"], request.remote_addr,request.sid))
        # Set the users socketid so that the user emit only sends data to this specific user.
        user = manager.get_user(session["uid"])
        if user:
            user.sid = request.sid
    except KeyError:
        logger.info("Got a connection but no session uid")
    return 

@socketio.on('disconnect')
def on_disconnect(): 
    try:
        #Remove users that left, if they take to long to come back they'll have to start over.
        user = manager.get_user(session["uid"])
        logger.info("User: {} disconnected".format(request.sid))
        if user is None:
            #This user does not even exist anymore -> delete him
            del session["uid"]    
        # else:
            #This user did not get a new sid in the meantime -> delete it
            # if request.sid == user.sid and user.uid != manager.app.config["SECRET_ADMIN_USERNAME"]:
            #     del manager.users[session["uid"]]
            #     del session["uid"]    
        return
    except KeyError:
        #Disconnect was triggered by server itself so we do not need to perform
        # clean up
        return

# @socketio.on_error_default  # handles all namespaces without an explicit error handler
# def default_error_handler(e):
#     logger.error("Socket error: ", e)
