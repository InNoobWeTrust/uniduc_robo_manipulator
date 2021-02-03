# Management hub

Flask server providing API to clients and manage remote robots via web socket.

Mostly follow REST API design guideline.

Currently, only robot control route is available.

```
<server_address>:<port>/api/v0/automata/
```

Some example requests can be found in [../client/sample_requests.rest](../client/sample_requests.rest). You should download the file or view raw text since Github render the file wrongly as markdown but it is not.

To test API, either use desktop application like Postman or search for "rest client" if using mobile device and follow their instructions. [Here is the instruction for Postman](https://learning.postman.com/docs/sending-requests/requests/#creating-requests)

**Notice**: The API described here is just for quick prototyping and may subject to changes. The plan is using some API design collaboration tool like [Insomnia](https://insomnia.rest/) to discuss and conclude on the final API as well as keeping universal specification (OpenAPI format).

## Authorization

To access api routes, use http basic authentication, provided email+password or token requested by sending a POST request to the endpoint below.

```
<server_address>:<port>/api/v0/tokens/
```

The recommended and more secure way is to authorize once using email+password to get token and then use token throughout the api routes. To renew, just use the very token at hand to request a new one.

Read more about http basic authentication here: [https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Authorization](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Authorization).

## Route nodes

1. `<server_address>:<port>/api/v0/automata/<serial_number>/ping`

    Ping the robot with specified serial number.

    HTTP methods allowed: `GET`

2. `<server_address>:<port>/api/v0/automata/<serial_number>/comports`

    Serial ports management for specified robot.

    HTTP methods allowed:

    - `GET`: List attached (connected) serial ports and its status (alive or not), attributes, protocol options.
    - `POST`: connect to specified serial port. If the port is already connected, disconnect and connect again with new attributes and protocol options. The json for request body must provide the port and optionally the attributes/protocol (currently, protocol options is not yet enabled). An example request is as follow:
        ```rest
        POST https://localhost:5000/api/v0/automata/dummy_serial/comports
        Accept: application/json
        content-type: application/json
        {
            "comport": "/dev/ttyUSB0",
            "attributes": {
                "baudrate": 9600,
                "parity": "PARITY_EVEN"
            },
            "protocol": {
                "terminator": "\r\n"
            }
        }
        ```
        + `comport`: the serial port to connect to.
        + `attributes`: attributes for serial connection
            * `baudrate`: the baudrate of serial com port to connect to.
            * `parity`: Enable parity checking.
            * others: see more at this link [https://pythonhosted.org/pyserial/pyserial_api.html](https://pythonhosted.org/pyserial/pyserial_api.html), Serial constructor.
        + `protocol`: message protocol override.
            * `cmd_mark`: mark the begin of session.
            * `encoding`: the encoding to use.
            * `encode_method`: set error handling scheme. See [https://www.w3schools.com/python/ref_string_encode.asp](https://www.w3schools.com/python/ref_string_encode.asp).
            * `terminator`: line-ending.
    - `PATCH`: close specified serial port. Example request is as follow:
        ```rest
        PATCH https://localhost:5000/api/v0/automata/dummy_serial/comports
        Accept: application/json
        content-type: application/json
        {
            "comport": "/dev/ttyUSB0"
        }
        ```
        + `comport`: the port to close.

3. `<server_address>:<port>/api/v0/automata/<serial_number>/physical_ports`
    List physical serial ports for specified robot.

    HTTP methods allowed:

    - `GET`: List available serial ports that can be discovered by PySerial. Won't list virtual ports such as those created by `socat`.

4. `<server_address>:<port>/api/v0/automata/<serial_number>/repl`

    Send command to serial connection and get the response.

    HTTP methods allowed: `POST`

    The json for request body must specify the serial port, session name and command to send. Optionally, provide timeout for response on serial port or timeout for API request as a whole. An example request would look like this:

    ```rest
    POST https://localhost:5000/api/v0/automata/dummy_serial/repl
    Accept: application/json
    content-type: application/json
    {
        "comport": "/dev/ttyUSB0",
        "timeout": 5,
        "session": "test",
        "cmd": "Hello\nRepl",
        "cmd_timeout": 3
    }
    ```
    - `comport`: the port to send command to.
    - `timeout`: the timeout for message session.
    - `session`: the name of the message session.
    - `cmd`: the command to send.
    - `cmd_timeout`: timeout for response from after command is sent to serial port.
