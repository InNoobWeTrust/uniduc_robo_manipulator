# Daemon service for robot

The daemon can be run as cli command or registered as system service to be run at boot.

## Socket connection

Require exporting to environment variables the address & port of management hub and the serial number of robot the service is running on.

For development and testing purpose, defaults values are set as follows:

```python
HUB_ADDR = os.getenv('HUB_ADDR') or 'http://localhost'
HUB_PORT = int(os.getenv('HUB_PORT') or '5000')
SERIAL_NUMBER = os.getenv('SERIAL_NUMBER') or 'dummy'
```

After connected to management hub, registered handlers will be triggered on corresponding events.

### Socket events

1. `connect`:

    Triggered on successful connection to management hub. Handler for this event will then emit a `join` event to request joining the room of its serial number (this is important). Management hub will then authorize the request and let robot join its room.

2. `disconnect`:

    Handle for doing tasks (log warning, emergency mode, etc...) when connection to server is down.

2. `ping`:

    This event is used for management hub to check the online status of daemon service on the robot.

    Accepted message type: anything, the message is just being logged, nothing more.

3. `comports`:

    Receive management command on concurrent serial connections the service is handling.

    Accepted message type: python dict with the below keys

    - `uuid`: The unique id for message, for checking timeout of socket response.
    - `content`: wrap the actual content. Sub keys:
        + `comport` - optional on specific commands: the target serial port
        + `attributes` - optional: serial connection attributes. If not specified, using pyserial's default with baudrate override of 9600 (to match defaults of Arduino boards). For details, see [here](https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial)
        + `protocol` - optional: connection protocol, allow overriding of the values below:
            - `cmd_mark`: The mark used to detect the data session begin and end. Default value is the exclamation mark `!`. Example: `!BEGIN <session_name>`
            - `encoding`: Encoding to encode/decode data. Default value is `ascii`, can also use `utf-8` if embedded board is programmed for it.
            - `encode_method`: Python's encode behavior on error. Default is 'replace'. For more details, see [here](https://www.w3schools.com/python/ref_string_encode.asp)
            - `terminator`: Line-ending separator. Default is `\n`.
        + `cmd` - required: The management command, available commands:
            - `list available`: List available real serial ports that we can connect.
            - `list attached`: List attached serial ports.
            - `connect`: connect to specified `comport` using `attributes` and `protocol`
            - `close`: close specified `comport`

4. `repl`:

    For sending command(s) to serial port and receive back the response.

    Accepted message type: python dict with the below keys

    - `uuid`: The unique id for message, for checking timeout of socket response.
    - `content`: wrap the actual content. Sub keys:
        + `comport` - required: Which connection to send the command(s) to.
        + `session` - required: The session name.
        + `cmd` - required: multi-lines command to send to serial.

## Serial connection protocol:

The convention for communication between this service and embedded board is as follow:

- Each session of send/receive must be wrapped with the specific mark and keyword, together with the session name.
- Default mark is `!`
- Keyword for session opening is `BEGIN`.
- Keyword for session closing is `END`.

Example session:

```
!BEGIN self destruct session
JUST
DO
IT
\!
!END self destruct session
```

Note that the mark is parsed from the beginning of the line, so be sure to escape that in the message (this strict checking could be removed if considered not practical).

### Limitation and known issues

- The sending of command session is blocking, once it is sent, protocol handler will wait until the line that mark the end of session or timeout. Must wait until the response is completed before sending another command. For simple usage, this should be enough. More advanced protocol can be developed later on practical needs.

- The threading read feature of pyserial is still experimental, there is a chance of faulty behaviour.
