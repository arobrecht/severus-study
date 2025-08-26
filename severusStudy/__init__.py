#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thur Dez 13 14:11:23 2018

@author: jpoeppel
"""
from pathlib import Path

try:
    import eventlet
    eventlet.monkey_patch()
except ImportError:
    pass

from flask import Flask
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

socketio = SocketIO() 
from .utils import Logger
logger = Logger()

from .manager import Manager
manager = Manager()
from glob import glob
from flask import current_app

def glob_assets(target):
    root = current_app.static_folder
    if root is None:
        return []    
    return [f[len(root)+1:].replace("\\", '/') for f in glob(root + '/' + target)]

def create_app(test_config=None):
    """
        Using the application factory pattern.
    """
    app = Flask(__name__, 
                instance_relative_config=True
                )
    
    app.jinja_env.globals.update(get_assets=glob_assets)
    app.config.from_object('config') #Will load config.py from root directory
    app.config.from_pyfile("config.py") #Will load instance config file
    app.debug = app.config["DEBUG"]
    if not app.config.get("EXPERIMENT_TYPE") or app.config["EXPERIMENT_TYPE"] not in ["initial", "baseline", "adaptive"]:
        raise RuntimeError("invalid EXPERIMENT_TYPE in config")

    app.wsgi_app = ProxyFix(app.wsgi_app)

    manager.app = app
    logger.set_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint, url_prefix=app.config["URL_PREFIX"])

    # If you run into problems of socket.io not connecting to flask properly, you can add 
    #cors_allowed_origins="*"
    # to the call below
    # TODO: remove cors placeholder!
    socketio.init_app(app, path=app.config["SOCKET_PATH"], cors_allowed_origins="*")
    return app
