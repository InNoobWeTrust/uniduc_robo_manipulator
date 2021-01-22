# -*- coding: utf-8 -*-
"""
Automata routes
"""

import json
import uuid
from datetime import datetime
from typing import Dict

from flask import current_app, jsonify, request
from flask_socketio import join_room, leave_room

from .. import socket_response_backend
# Import api blueprint from parent (circular dependency)
from . import api, socketio


@socketio.on('connect')
def socket_connect():
    """
    Robot connection to server is established here.
    Need to validate and allow only registered robots.
    """
    current_app.logger.debug(f'{request.args}')
    if True:  # TODO: Only allow registered robots
        current_app.logger.info(f'Authorized robot connected')
        # Keep records of online robots
        socket_response_backend.sadd('online', request.sid)
    else:
        current_app.logger.info(f'Unauthorized device rejected')
        raise ConnectionRefusedError('authentication failed')


@socketio.on('disconnect')
def socket_disconnect():
    current_app.logger.info('Robot disconnected: {request.authorization}')
    # Remove from records of online robots
    socket_response_backend.srem('online', request.sid)


@socketio.on('join')
def socket_room_join(message: Dict):
    """
    After connected, robot will request to join room named its serial number
    """
    # TODO: Allow joining authorized rooms only
    join_room(message['serial_number'])
    # Keep records of robots which are on duty
    socket_response_backend.hset(
        'on_duty',
        request.sid,
        message['serial_number'],
    )
    current_app.logger.info(
        f'Robot with serial number <{message["serial_number"]}> is ready')


@socketio.on('leave')
def socket_room_leave(message: Dict):
    """
    When service on robot is shutting down, robot will request to leave room
    """
    # TODO: Update the database of online robots
    leave_room(message['serial_number'])
    # Remove from records of on-duty robots
    socket_response_backend.hdel('on_duty', request.sid)
    current_app.logger.info(
        f'Robot with serial number <{message["serial_number"]}> '
        'is shutting down')


@socketio.on('response')
def socket_response(message: Dict):
    """
    Handle responses from robots, uuid in the response is tied with
    corresponding request.
    """
    current_app.logger.debug(f'Received socket message response'
                             f'\n{message}')
    state = socket_response_backend.hget('message_session',
                                         message['request']['uuid'])
    state = json.loads(state)
    # Update status for message response
    state['status'] = 'responded'
    state['respond_time'] = datetime.timestamp(datetime.now())
    state['response'] = message['response']
    socket_response_backend.hset('message_session', message['request']['uuid'],
                                 json.dumps(state))


def socket_send_async(action: str, message: Dict, room: str, timeout=5):
    """
    Send socket message and get back the session information to retrieve
    response asynchronously.
    TODO: Spawn delayed celery task to delete expired session from Redis.
    """
    # TODO: uuid can rarely be duplicated, validate before use
    u = str(uuid.uuid4())
    socket_message = {
        'uuid': u,
        'content': message,
    }
    current_app.logger.debug(f'Sending socket message for action "{action}"'
                             f'\n{socket_message}')
    socketio.emit(action, socket_message, room=room)
    state = {
        'session': u,
        'request': message,
        'status': 'sent',
        'send_time': datetime.timestamp(datetime.now()),
        'timeout': timeout,
    }
    # Keep track of the status
    socket_response_backend.hset('message_session', u, json.dumps(state))
    response = jsonify(state)
    response.status_code = 200
    return response


@api.route('/automata/message_session/<session_id>', methods=['GET'])
def message_session(session_id):
    """
    Get the state of message session
    """
    state = socket_response_backend.hget('message_session', session_id)
    if state is None:
        response = jsonify({
            'error': 'session not exist or expired',
        })
    else:
        response = jsonify(json.loads(state))
    response.status_code = 200
    return response


@api.route('/automata/<serial_number>/ping')
def ping(serial_number: str):
    """
    Check if robot with specified serial number is online yet.
    """
    return socket_send_async('ping', 'ping', room=serial_number)


@api.route('/automata/<serial_number>/physical_ports', methods=['GET'])
def physical_ports(serial_number: str):
    """
    List available comports.
    """
    message = {'cmd': 'list available'}
    timeout = int(request.json.get('timeout', 5)) if request.get_json(
        silent=True) else 5
    return socket_send_async('comports',
                             message,
                             room=serial_number,
                             timeout=timeout)


@api.route('/automata/<serial_number>/comports',
           methods=['GET', 'POST', 'PATCH'])
def comports(serial_number: str):
    """
    GET: List attached comports.
    POST: Connect new comport or replace old connection with new setup values.
    PATCH: Disconnect comport. This is counter-intuitive but as DELETE is not
           accepting request body, this is the only choice
    """
    message = {}
    timeout = int(request.json.get('timeout', 5)) if request.get_json(
        silent=True) else 5
    if request.method == 'GET':
        message = {'cmd': 'list attached'}
    elif request.method == 'POST':
        message = {
            'cmd': 'connect',
            'comport': request.json["comport"],
            'attributes': request.json["attributes"]
        }
    elif request.method == 'PATCH':
        message = {'cmd': 'close', 'comport': request.json["comport"]}
    return socket_send_async('comports',
                             message,
                             room=serial_number,
                             timeout=timeout)


@api.route('/automata/<serial_number>/repl', methods=['POST'])
def repl(serial_number: str):
    """
    Send control request to robot of specific serial number.
    Since robots at least will join to the room of their serial number, send
    request to the room is enough.
    """
    message = {
        'comport': request.json['comport'],
        'session': request.json['session'],
        'cmd': request.json['cmd'],
        'timeout': int(request.json.get('cmd_timeout', 5))
    }
    timeout = int(request.json.get('timeout')) or 5
    return socket_send_async('repl',
                             message,
                             room=serial_number,
                             timeout=timeout)
