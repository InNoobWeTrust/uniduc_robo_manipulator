#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Control service using socketio
"""

import logging
import os
import queue
import sys
import threading
from typing import Dict, List, Type

import serial
import socketio
from serial.threaded import Protocol, ReaderThread
from serial.tools import list_ports

# Address to api server, should use static IP on production server
HUB_ADDR = os.getenv('HUB_ADDR') or 'http://localhost'
HUB_PORT = int(os.getenv('HUB_PORT') or '5000')
# Provide serial number as unique id for robot
SERIAL_NUMBER = os.getenv('SERIAL_NUMBER') or 'dummy'

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class AutomataProtocol(Protocol):
    """
    Protocol for simultaneously reading serial device
    """
    def __init__(self,
                 logger: Type[logging.Logger],
                 cmd_mark='!',
                 encoding='ascii',
                 encode_method='replace',
                 terminator='\n'):
        super(AutomataProtocol, self).__init__()
        self.logger = logger
        self.cmd_mark = cmd_mark  # For event processing
        self.encoding = encoding
        self.encode_method = encode_method
        self.terminator = terminator
        self.responses = queue.Queue()
        self.events = queue.Queue()
        self.pending_line = ''
        self.session = None
        self.lock = threading.Lock()
        self.transport = None

    def connection_made(self, transport):
        """
        Protocol interface
        """
        self.transport = transport

    def connection_lost(self, exc):
        """
        Protocol interface
        """
        self.transport = None
        super(AutomataProtocol, self).connection_lost(exc)

    def _batch_begin(self, line: str):
        event = None
        if self.session is not None:
            # Faulty device, yield error event
            event = {
                'error': 'Faulty response (nested BEGIN)',
                'trace': line,
            }
            self.logger.fatal(event)
            self.session = None
        else:
            self.session = line[len(f'{self.cmd_mark}BEGIN '):]
            event = {
                'event': 'begin',
                'session': self.session,
            }
            self.logger.debug(event)
        # Store event
        self.events.put(event)

    def _batch_end(self, line: str):
        session = line[len(f'{self.cmd_mark}END '):]
        event = None
        if self.session is None:
            # Faulty device, yield error event
            event = {
                'error': 'Faulty response (END without BEGIN)',
                'trace': line,
            }
            self.logger.fatal(event)
        elif self.session != session:
            self.session = None
            event = {
                'error': 'Faulty response (unknown id)',
                'trace': line,
            }
            self.logger.debug(event)
        else:
            event = {
                'event': 'end',
                'session': self.session,
            }
            self.session = None
        # Store event
        self.events.put(event)

    def _process_line(self, line: str):
        self.responses.put(line)
        # Simple integrity verification
        if line.startswith(f'{self.cmd_mark}BEGIN'):
            self._batch_begin(line)
        elif line.startswith(f'{self.cmd_mark}END'):
            self._batch_end(line)
        elif line.startswith(self.cmd_mark):
            self.events.put({
                'error': 'Faulty response (unknown mark)',
                'trace': line,
            })

    def data_received(self, data):
        """
        Protocol interface
        """
        # Join with pending line and split by terminator
        raw = data.decode(self.encoding)
        self.logger.debug(f'Serial received raw data: {raw}')
        buf = self.pending_line + raw
        lines = buf.split(self.terminator)
        self.logger.debug(f'Processed lines: {lines}')
        self.pending_line = lines[-1] if len(lines) > 0 else ''
        for line in lines[:-1]:
            self._process_line(line)

    def send_cmd(self, session: str, cmd: str, timeout: int) -> Dict:
        """
        Send command and wait for batch responses from events
        """
        encapsulated = (f'{self.cmd_mark}BEGIN {session}{self.terminator}'
                        f'{cmd}{self.terminator}'
                        f'{self.cmd_mark}END {session}{self.terminator}')
        self.logger.debug(encapsulated)
        with self.lock:
            # Clear pending line to prevent conflict
            self.pending_line = ''
            self.transport.write(
                encapsulated.encode(self.encoding, self.encode_method))
            responses = []
            events = []
            while True:
                # Waiting for end event
                try:
                    event = self.events.get(timeout=timeout)
                    events.append(event)
                    if event.get('event') and event['event'] == 'end':
                        break
                except queue.Empty:
                    events.append({
                        'error':
                        f'Timeout with no end mark after {timeout}s',
                    })
                    break
            while True:
                # Getting all responses up till now
                try:
                    responses.append(self.responses.get_nowait())
                except queue.Empty:
                    break
            return {
                'result': self.terminator.join(responses),
                'events': events,
            }


class ControlSocket:
    """
    Wrapper to socketio connection for remote communication to serial device
    """
    def __init__(self, hub_addr: str, hub_port: int, serial_number: str):
        self.hub = {'addr': hub_addr, 'port': hub_port}
        self.serial_number = serial_number
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.sio = None
        self.serial_threads = {}

    def _available_comports(self) -> Dict:
        """
        Get available serial ports
        """
        try:
            return {
                'result': [
                    comport.__dict__
                    for comport in list_ports.comports(include_links=True)
                ]
            }
        except:
            return {
                'error': 'Cannot list comports',
            }

    def _connected_comports(self) -> Dict[str, List[Dict]]:
        """
        List currently attached comports.
        """
        return {
            'result': [{
                'comport': path,
                'alive': port['protocol'].transport is not None,
                'attributes': port['attributes'],
                'protocol': {
                    'cmd_mark': port['protocol'].cmd_mark,
                    'encoding': port['protocol'].encoding,
                    'encode_method': port['protocol'].encode_method,
                    'terminator': port['protocol'].terminator,
                },
            } for path, port in self.serial_threads.items()]
        }

    def _connect_comport(self, comport: str, attributes: Dict,
                         protocol: Dict) -> Dict[str, str]:
        """
        Connect to specified serial comport.
        """
        if comport in self.serial_threads:
            # Connect again with new attributes
            # Closing current connection first
            self._close_comport(comport)
        self.logger.debug(f'Connecting to {comport}...')
        ser = serial.serial_for_url(comport, **attributes)
        reader = ReaderThread(
            ser, lambda: AutomataProtocol(logger=self.logger, **protocol))
        reader.start()
        transport, protocol = reader.connect()
        self.serial_threads[comport] = {
            'attributes': attributes,
            'reader': reader,
            'transport': transport,
            'protocol': protocol,
        }
        return {
            'result': f'{comport} connected successfully',
        }

    def _close_comport(self, comport: str) -> Dict[str, str]:
        """
        Close specified serial comport.
        """
        if comport in self.serial_threads:
            self.logger.debug(f'Closing {comport}...')
            self.serial_threads[comport]['reader'].close()
            del self.serial_threads[comport]
            return {
                'result': f'{comport} closed successfully',
            }
        else:
            self.logger.warn(f'{comport} not yet attached')
            return {
                'error': f'{comport} not attached',
            }

    def _comport_repl(self, session: str, cmd: str, comport: str,
                      timeout: int) -> Dict:
        """
        Send request to serial and get response
        """
        if comport not in self.serial_threads:
            return {
                'error': f'{comport} not attached',
            }
        else:
            return self.serial_threads[comport]['protocol'].send_cmd(
                session, cmd, timeout=timeout)

    def serve(self):
        """
        Start service
        """
        self.sio = socketio.Client(logger=self.logger,
                                   engineio_logger=self.logger)

        @self.sio.event
        def connect():
            self.logger.debug('Connection established, joining serial room')
            # Join serial room
            self.sio.emit('join', {'serial_number': self.serial_number})

        @self.sio.event
        def ping(message: str):
            self.logger.debug(f'Received ping message: {message}')
            self.sio.emit('response', {
                'request': message,
                'response': 'pong',
            })

        @self.sio.event
        def comports(message: Dict):
            self.logger.debug(f'Received comports message: {message}')
            cmd: str = message['content']['cmd']
            comport: str = message['content'].get('comport') or None
            # Default attributes follows Arduino's default
            attributes: Dict = message['content'].get('attributes') or {
                'baudrate': 9600,
            }
            protocol: Dict = message['content'].get('protocol') or {}
            response = {
                'error': 'Invalid request received from server',
            }
            if cmd == 'list available':
                self.logger.debug('Listing available comports')
                response = self._available_comports()
            elif cmd == 'list attached':
                self.logger.debug('Listing connected comports')
                response = self._connected_comports()
            elif cmd == 'connect' and comport is not None:
                self.logger.debug(f'Attempt connecting to {comport} '
                                  f'with attributes {attributes} '
                                  f'and protocol override {protocol}...')
                response = self._connect_comport(comport=comport,
                                                 attributes=attributes,
                                                 protocol=protocol)
            elif cmd == 'close' and comport is not None:
                self.logger.debug(f'Attempt closing {comport}...')
                response = self._close_comport(comport)
            self.sio.emit('response', {
                'request': message,
                'response': response,
            })

        @self.sio.event
        def repl(message: Dict):
            self.logger.debug(f'Received repl message: {message}')
            comport = message['content']['comport']
            session = message['content']['session']
            cmd = message['content']['cmd']
            timeout = int(message['content'].get('timeout', 5))
            if self.serial_threads[comport]['protocol'].transport is not None:
                response = self._comport_repl(session=session,
                                              cmd=cmd,
                                              comport=comport,
                                              timeout=timeout)
            else:
                response = {'error': f'connection to {comport} is dead'}
            self.sio.emit('response', {
                'request': message,
                'response': response,
            })

        @self.sio.event
        def disconnect():
            self.logger.debug('Disconnected from server')

        self.sio.connect(f'{self.hub["addr"]}:{self.hub["port"]}')
        self.sio.wait()


def serve(hub_addr=HUB_ADDR, hub_port=HUB_PORT, serial_number=SERIAL_NUMBER):
    ControlSocket(hub_addr=hub_addr,
                  hub_port=hub_port,
                  serial_number=serial_number).serve()


if __name__ == '__main__':
    serve()
