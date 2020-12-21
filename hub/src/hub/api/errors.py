# -*- coding: utf-8 -*-

"""
Errors handling
"""

from flask import jsonify
# Import api blueprint from parent
from . import api


@api.errorhandler(404)
def not_found(e):
    response = jsonify({'error': 'not found'})
    response.status_code = 404
    return response
