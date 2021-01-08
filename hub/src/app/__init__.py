# -*- coding: utf-8 -*-
"""
Entry point for server
"""

import os

import eventlet
from config import config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Patch eventlet first before importing project's code
eventlet.monkey_patch()

db = SQLAlchemy()


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    # Redirect http traffic to https on production
    if app.config['SSL_REDIRECT']:
        from flask_sslify import SSLify
        app = SSLify(app)

    # Register blueprints and routes
    from .api_0_1 import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v0')
    # Only possible way to specify message queue is to do here.
    # Ref: https://github.com/miguelgrinberg/Flask-SocketIO/issues/618#issuecomment-722645749
    from .api_0_1 import socketio
    socketio.init_app(app,
                      async_mode='eventlet',
                      message_queue=app.config['MESSAGE_QUEUE'])

    return app, socketio
