# -*- coding: utf-8 -*-
"""
Automata routes
"""

import uuid

from eventlet import event
from eventlet.timeout import Timeout
from flask import current_app, jsonify, request
from flask_socketio import join_room, leave_room

# Import api blueprint from parent (circular dependency)
from . import api, socketio

# Events for waiting response from robot after sending request
events = {}


@socketio.on('connect')
def socket_connect():
    """
    Robot connection to server is established here.
    Need to validate and allow only registered robots.
    """
    current_app.logger.debug(f'{request.args}')
    if True:  # TODO: Only allow registered robots
        current_app.logger.info(f'Authorized robot connected')
    else:
        current_app.logger.info(f'Unauthorized device rejected')
        raise ConnectionRefusedError('authentication failed')


@socketio.on('disconnect')
def socket_disconnect():
    current_app.logger.info('Robot disconnected: {request.authorization}')


@socketio.on('join')
def socket_room_join(message):
    """
    After connected, robot will request to join room named its serial number
    """
    # TODO: Allow joining authorized rooms only
    join_room(message['serial_number'])
    current_app.logger.info(
        f'Robot with serial number <{message["serial_number"]}> is ready')


@socketio.on('leave')
def socket_room_leave(message):
    """
    When service on robot is shutting down, robot will request to leave room
    """
    # TODO: Update the database of online robots
    leave_room(message['serial_number'])
    current_app.logger.info(
        f'Robot with serial number <{message["serial_number"]}> '
        'is shutting down')


@socketio.on('response')
def socket_response(message):
    """
    Handle responses from robots, uuid in the response is tied with
    corresponding request.
    """
    current_app.logger.debug(f'Received socket message response'
                             f'\n{message}')
    try:
        e = events[message['request']['uuid']]
        e.send(message)
    except KeyError:
        pass


def socket_send_receive(action, message, room, timeout=5):
    u = str(uuid.uuid4())
    socket_message = {
        'uuid': u,
        'content': message,
    }
    current_app.logger.debug(f'Sending socket message for action "{action}"'
                             f'\n{socket_message}')
    socketio.emit(action, socket_message, room=room)
    timer = Timeout(timeout)
    socket_response = None
    try:
        e = events[u] = event.Event()
        socket_response = e.wait()
    except Timeout:
        # abort(504)
        socket_response = {'error': f'request timed out after {timeout}s'}
        pass
    finally:
        events.pop(u, None)
        timer.cancel()
    response = jsonify(socket_response)
    response.status_code = 404 if socket_response.get('error') else 200
    return response


@api.route('/automata/<serial_number>/ping')
def ping(serial_number):
    """
    Check if robot with specified serial number is online yet.
    """
    return socket_send_receive('ping', 'ping', room=serial_number)


@api.route('/automata/<serial_number>/comports',
           methods=['OPTIONS', 'GET', 'POST', 'PATCH'])
def comports(serial_number):
    """
    OPTIONS: List available comports.
    GET: List attached comports.
    POST: Connect new comport or replace old connection with new setup values.
    PATCH: Disconnect comport. This is counter-intuitive but as DELETE is not
           accepting request body, this is the only choice
    """
    message = ''
    timeout = int(request.json.get('timeout', 5)) if request.get_json(
        silent=True) else 5
    if request.method == 'OPTIONS':
        message = {'cmd': 'list available'}
    elif request.method == 'GET':
        message = {'cmd': 'list attached'}
    elif request.method == 'POST':
        message = {
            'cmd': 'connect',
            'comport': request.json["comport"],
            'attributes': request.json["attributes"]
        }
    elif request.method == 'PATCH':
        message = {'cmd': 'close', 'comport': request.json["comport"]}
    return socket_send_receive('comports',
                               message,
                               room=serial_number,
                               timeout=timeout)


@api.route('/automata/<serial_number>/repl', methods=['POST'])
def repl(serial_number):
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
    return socket_send_receive('repl',
                               message,
                               room=serial_number,
                               timeout=timeout)
