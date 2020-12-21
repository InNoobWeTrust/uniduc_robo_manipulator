# -*- coding: utf-8 -*-
"""
Control service using socketio
"""

import os
import logging
import socketio

# Address to api server, should use static IP on production server
# HUB_ADDR = os.environ.get('HUB_ADDR', 'https://api.uniduc.com')
HUB_ADDR = os.environ.get('HUB_ADDR', 'http://localhost')
HUB_PORT = int(os.environ.get('HUB_PORT', '55271'))
# Provide serial number as unique id for robot
SERIAL_NUMBER = os.environ.get('SERIAL_NUMBER', 'dummy')


def serve(hub_addr=HUB_ADDR, hub_port=HUB_PORT, serial=SERIAL_NUMBER):
    sio = socketio.Client(logger=True, engineio_logger=True)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    @sio.event
    def connect():
        logger.debug('Connection established, joining serial room')
        # Join serial room
        sio.emit('join', {'serial': serial})

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

    sio.connect(f'{hub_addr}:{hub_port}')
    sio.wait()


if __name__ == '__main__':
    serve()
