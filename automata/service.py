# -*- coding: utf-8 -*-
"""
Control service using socketio
"""

import os
import logging
import socketio

# Address to api server, should use static IP on production server
# HUB_ADDR = 'http://api.uniduc.com'
HUB_ADDR = 'http://localhost'
HUB_PORT = 55271
# Must provide serial number for running this service
SERIAL_NUMBER = os.environ.get('SERIAL_NUMBER', 'dummy')

sio = socketio.Client(logger=True, engineio_logger=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@sio.event
def connect():
    logger.debug('Connection established, joining serial room')
    # Join serial room
    sio.emit('join', {'serial': SERIAL_NUMBER})


@sio.event
def ping(message):
    logger.debug(f'Received ping message: {message}')
    sio.emit('response', {
        'request': message,
        'response': 'pong',
    })


@sio.event
def manipulate(message):
    logger.debug('Received control message:\n{message}')
    # TODO: Pass the request to file descriptor of USB UART
    sio.emit('response', {
        'request': message,
        'response': 'done',
    })


@sio.event
def sensors(messsage):
    logger.debug('Received sensors request message:\n', messsage)
    # TODO: Pass the request to file descriptor of USB UART
    # Send back sensors read result to hub
    sio.emit('response', {
        'request': messsage,
        'response': 'Lorem ipsum dolor sit amet'
    })


@sio.event
def disconnect():
    logger.debug('Disconnected from server')


sio.connect(f'{HUB_ADDR}:{HUB_PORT}')
sio.wait()
