#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot control service
    - Publish movement control message on ROS topic: /automata/movement
    - Communication with management server using socketio
"""

import logging
import os
import sys
from time import sleep

import rospy
import socketio
from geometry_msgs import Twist, Vector3

# Address to api server, should use static IP on production server
HUB_ADDR = os.getenv('HUB_ADDR') or 'http://localhost'
HUB_PORT = int(os.getenv('HUB_PORT') or '5000')
# Provide serial number as unique id for robot
SERIAL_NUMBER = os.getenv('SERIAL_NUMBER') or 'dummy'

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class MovementPublisher:
    """
    Movement control
    """
    def __init__(self):
        self.pub = rospy.Publisher('/automata/movement', Twist, queue_size=10)

    def move(self, linear, angular):
        movement = Twist()
        movement.linear = Vector3()
        movement.linear.x = linear[0]
        movement.linear.y = linear[1]
        movement.linear.z = linear[2]
        movement.angular = Vector3()
        movement.angular.x = linear[0]
        movement.angular.y = linear[1]
        movement.angular.z = linear[2]
        self.pub.publish(movement)


class SocketClient:
    """
    Wrap socketio connection for remote communication
    """
    def __init__(self, hub_addr, hub_port, serial_number):
        self.hub = {'addr': hub_addr, 'port': hub_port}
        self.serial_number = serial_number
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.sio = socketio.Client(logger=self.logger,
                                   engineio_logger=self.logger)
        self.movement_ctl = MovementPublisher()

        @self.sio.event
        def connect():
            self.logger.debug('Connection established, joining serial room')
            # Join serial room
            self.sio.emit('join', {'serial_number': self.serial_number})

        @self.sio.event
        def ping(message):
            self.logger.debug('Received ping message: {}'.format(message))
            self.sio.emit('response', {
                'request': message,
                'response': 'pong',
            })

        @self.sio.event
        def move(message):
            self.movement_ctl.move(linear=message[0], angular=message[1])

        @self.sio.event
        def disconnect():
            self.logger.debug('Disconnected from server')

    def serve(self):
        while True:
            try:
                self.sio.connect('{}:{}'.format(self.hub["addr"],
                                                self.hub["port"]))
                break
            except KeyboardInterrupt:
                exit(1)
            except:
                self.logger.info('Server is down, wait 5s before reconnect...')
                sleep(5)

    def __del__(self):
        """
        Gracefully disconnect to hub
        """
        self.sio.disconnect()


def serve(hub_addr=HUB_ADDR, hub_port=HUB_PORT, serial_number=SERIAL_NUMBER):
    rospy.init_node('automata', anonymous=True)
    SocketClient(hub_addr=hub_addr,
                 hub_port=hub_port,
                 serial_number=serial_number).serve()
    # Keeps python from exiting until this node is stopped
    rospy.spin()


if __name__ == '__main__':
    serve()
