# Robot management suite for Uniduc

The suite contains 3 sub projects:

- Daemon service on robot: Communicate with management hub via web socket. Allow remote control, status report and maintenance.
- Management hub: Manage robots via web sockets. Provide API to clients.
- Clients: TBD, but initial choice was to design with [Figma](https://www.figma.com/prototyping/) and export to [Flutter](https://flutter.dev/) code, then build crossplatform clients from that. Ideally, the clients should be available on web, mobile, desktop and optionally on home-grown handheld device specialized for Uniduc's products (for best support experience).

Daemon service and management hub is developed using python as main programming language to ease code maintenance and integration with development of robot's intelligence.

## **Important notice**

Currently the deploy feature is not ready, so before running the service or management hub on target machine, execute the script `setup_dev_environment.sh` to install `poetry` and load dependencies.

```shell
./setup_dev_environment.sh
```

The ability to change port of management hub is also broken, so the port will always be 55271 (or any other port you see in the log when management hub is starting). Until the problem is resolved, please be notice of this minor bug.

---

## Management hub

### Setting up database

API routes require authorization to access so user information must be stored in database. Before using management hub, database needs to be initiated. Follow the steps bellow to setup development database:

```shell
cd ./hub
FLASK_APP=hub.py poetry run flask shell
```

When inside the shell, execute commands below to setup fake database

```python3
from hub import db, User, Robot, RoboticRole, RobotUser
db.drop_all()
db.create_all()
User.generate_fake(10)
Robot.generate_fake()
RoboticRole.insert_roles()
RobotUser.generate_fake()
quit()
```

### Running

Change dir to `./hub` and execute the following:

```shell
# Install required dependencies
sudo ./install_dependencies.sh
# Provide the HUB_ADDR with only the IP, HUB_PORT with the port and run
HUB_ADDR=0.0.0.0 HUB_PORT=5000 poetry run python3 src//hub.py
```

_**Didn't work?**_: refer to the general notice to ensure poetry is installed and all dependencies are loaded.

### Main dependencies to refer to for development:

- Flask: Lightweight web server with extensibility, chosen because this is the one familiar with ML/DL practitioners. [[Documentation](https://flask.palletsprojects.com/)]
- Flask-socketio: Integrate SocketIO to server. [[Documentation](https://flask-socketio.readthedocs.io/en/latest/)]

For detailed documentation on this sub-project, [see here](docs/management_hub.md)

## Daemon service:

### Running

**Note**: management hub must be started first in order to let service connect.

To run the service in development mode, change dir to `./automata` and execute the command below:

```shell
# Provide correct http address and port to management hub via environment variables, example: http://localhost
# Also, change the serial number of the robot via enviroment variable `SERIAL_NUMBER`
HUB_ADDR=http://localhost HUB_PORT=5000 SERIAL_NUMBER='ultron' poetry run serve
```

_**Didn't work?**_: refer to the general notice to ensure poetry is installed and all dependencies are loaded.

### Main dependencies to refer to for development:

- python-socketio: For communication with management hub. [[Documentation](https://python-socketio.readthedocs.io/en/latest/)]
- pyserial: For communication via serial connection with embedded boards such as Arduino, which will control actuator, reading sensors, etc...

[ ] **TODO**: Additionally, this sub-project contains a small python library for streaming the annotated camera image to udp stream using GStreamer.

For detailed documentation on this sub-project, [see here](docs/automata_service.md)

## Clients

**TBD**