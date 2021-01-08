# -*- coding: utf-8 -*-
"""
Errors handling
"""

from flask import jsonify
from app.exceptions import ValidationError
# Import api blueprint from parent
from . import api


def bad_request(message):
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message):
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


def forbidden(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response


@api.errorhandler(404)
def not_found(e):
    response = jsonify({'error': 'not found'})
    response.status_code = 404
    return response


@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])
