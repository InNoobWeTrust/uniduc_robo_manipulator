# -*- coding: utf-8 -*-
"""
Automata routes
"""

import uuid
from eventlet import event
from eventlet.timeout import Timeout
from flask import current_app, request, jsonify
from flask_socketio import join_room
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
        current_app.logger.info(
            f'Unauthorized device rejected')
        raise ConnectionRefusedError('authentication failed')


@socketio.on('disconnect')
def socket_disconnect():
    current_app.logger.info('Robot disconnected: {request.authorization}')


@socketio.on('join')
def socket_room_join(message):
    """
    After connected, robot will request to join a serial room
    """
    # TODO: Allow joining authorized rooms only
    join_room(message['serial'])
    current_app.logger.info(
        f'Robot with serial number <{message["serial"]}> is ready')


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


def socket_send_receive(action, message, room, timeout=3):
    u = str(uuid.uuid4())
    socket_message = {
        'uuid': u,
        'message': message,
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
        socket_response = {'error': 'request timed out'}
        pass
    finally:
        events.pop(u, None)
        timer.cancel()
    response = jsonify(socket_response)
    response.status_code = 404 if socket_response.get('error') else 200
    return response


@api.route('/automata/<serial>/ping')
def ping(serial):
    """
    Check if robot with specified serial number is online yet.
    """
    return socket_send_receive('ping', 'ping', room=serial)


@api.route('/automata/<serial>/manipulate', methods=['POST'])
def manipulate(serial):
    """
    Send control request to robot of specific serial number.
    Since robots at least will join to the room of their serial number, send
    request to the room is enough.
    """
    return socket_send_receive('manipulate', request.json['cmd'], room=serial)


@api.route('/automata/<serial>/sensors', methods=['POST'])
def sensors(serial):
    """
    Send sensors request to robot of specific serial number.
    Since robots at least will join to the room of their serial number, send
    request to the room is enough.
    """
    return socket_send_receive('sensors', request.json['cmd'], room=serial)
