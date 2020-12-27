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

## Route nodes (adding these suffix to the route above)

1. `<serial_number>/ping`

    Ping the robot with specified serial number.

    HTTP methods allowed: `GET`

2. `<serial_number>/comports`

    Serial ports management for specified robot.

    HTTP methods allowed:

    - `OPTIONS`: List available serial ports that can be discovered by PySerial. Won't list virtual ports such as those created by `socat`.
    - `GET`: List attached (connected) serial ports and its status (alive or not), attributes, protocol options.
    - `POST`: connect to specified serial port. If the port is already connected, disconnect and connect again with new attributes and protocol options. The json for request body must provide the port and optionally the attributes/protocol (currently, protocol options is not yet enabled). An example request is as follow:
        ```rest
        POST https://127.0.0.1:55271/automata/dummy_serial/comports
        Accept: application/json
        content-type: applicatation/json
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
    - `PATCH`: close specified serial port. Example request is as follow:
        ```rest
        PATCH https://127.0.0.1:55271/automata/dummy_serial/comports
        Accept: application/json
        content-type: applicatation/json
        {
            "comport": "/dev/ttyUSB0"
        }
        ```

3. `<serial_number>/repl`

    Send command to serial connection and get the response.

    HTTP methods allowed: `POST`

    The json for request body must specify the serial port, session name and command to send. Optionally, provide timeout for response on serial port or timeout for API request as a whole. An example request would look like this:

    ```rest
    POST https://127.0.0.1:55271/automata/dummy_serial/repl
    Accept: application/json
    content-type: applicatation/json
    {
        "comport": "/dev/ttyUSB0",
        "timeout": 5,
        "session": "test",
        "cmd": "Hello\nRepl",
        "cmd_timeout": 3
    }
    ```