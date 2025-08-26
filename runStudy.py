from pathlib import Path

try:
    # Eventlet wants to perform some monkey patching. 
    # In some cases, there are more specialized patches 
    # (e.g. only for threads) that may be sufficient, but
    # this usually does not break anything
    import eventlet
    eventlet.monkey_patch()
except ImportError:
    pass

from severusStudy import create_app, socketio

# We need to create our app instance here, so that other webservers 
# (e.g. gunicorn) can find and use it.
# TODO: apart from the gunicorn compatibility issue, read up socket.ios recommendations here:
# https://flask-socketio.readthedocs.io/en/latest/deployment.html
app = create_app()

if __name__ == "__main__":
    # When we use socketio for websockets, we need to start the development
    # server via socketio instead of directly using app.run()
    # compute and store word embeddings of ontology
    app.logger.debug("Starting development server with socketio")
    print(app.config)
    socketio.run(app, host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])
