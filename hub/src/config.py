# -*- coding: utf-8 -*-
"""
Config file for server
"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'omaewamoushindeiru'
    HUB_ADDR = os.getenv('HUB_ADDR') or 'localhost'
    HUB_PORT = int(os.getenv('HUB_PORT') or '5000')
    ADMIN_USER = os.getenv('ADMIN_USER')  # Must be set in environment
    ADMIN_PWD = os.getenv('ADMIN_PWD')  # Must be set in environment
    SSL_REDIRECT = False  # Default is not using SSL
    MESSAGE_QUEUE = os.getenv('MESSAGE_QUEUE') or 'redis://localhost:6379/0'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass


class DevConfig(Config):
    DEBUG = True
    ADMIN_USER = os.getenv('ADMIN_USER') or 'root'
    ADMIN_PWD = os.getenv('ADMIN_PWD') or 'toor'
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DEV_DATABASE_URL'
    ) or f'sqlite:///{os.path.join(basedir, "data-dev.sqlite")}'


class TestConfig(Config):
    TESTING = True
    ADMIN_USER = os.getenv('ADMIN_USER') or 'admin'
    ADMIN_PWD = os.getenv('ADMIN_PWD') or 'admin'
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL') or 'sqlite://'


class Productionconfig(Config):
    SSL_REDIRECT = True  # Enable SSL on production server
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL') or f'sqlite:///{os.path.join(basedir, "data.sqlite")}'

    @classmethod
    def init_app(cls, app):
        # Handle reverse proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)


config = {
    'dev': DevConfig,
    'test': TestConfig,
    'production': Productionconfig,
    'default': DevConfig,
}
