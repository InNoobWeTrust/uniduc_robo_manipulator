# -*- coding: utf-8 -*-
"""
Main script
"""

import os

from dotenv import load_dotenv

# Load dotenv file before importing app's code
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from app import create_app, db
from app.models import Robot, RoboticPermission, RoboticRole, RobotUser, User
from flask_migrate import Migrate

app, socketio = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db,
                RoboticPermission=RoboticPermission,
                RoboticRole=RoboticRole,
                Robot=Robot,
                RobotUser=RobotUser,
                User=User)


@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # migrate database to latest revision
    upgrade()


if __name__ == '__main__':
    socketio.run(app, host=os.getenv('HUB_ADDR'), port=os.getenv('HUB_PORT'))
