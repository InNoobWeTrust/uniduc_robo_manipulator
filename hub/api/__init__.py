# -*- coding: utf-8 -*-
"""
API module
"""

from flask import Blueprint
from flask_socketio import SocketIO


# Must create blueprint before importing routes
api = Blueprint('api', __name__)
socketio = SocketIO()

# Import routes, using the blueprint created (circular dependencies)
from . import automata, errors
