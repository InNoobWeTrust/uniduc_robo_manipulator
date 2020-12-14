# -*- coding: utf-8 -*-
"""
Entry point for server
"""

import os
from flask import Flask
import eventlet
eventlet.monkey_patch()
from config import config
from api import api as api_blueprint, socketio


def create_hub(config_name='default'):
    hub = Flask(__name__)
    hub.config.from_object(config[config_name])
    config[config_name].init_app(hub)

    # Register blueprints and routes
    hub.register_blueprint(api_blueprint, url_prefix='/api/v0')
    socketio.init_app(hub)

    return hub


if __name__ == '__main__':
    config_name = os.environ.get('FLASK_CONFIG', 'default')
    hub = create_hub(config_name)
    socketio.run(hub,
                 host=config[config_name].HUB_ADDR,
                 port=config[config_name].HUB_PORT)
