# -*- coding: utf-8 -*-

"""
Config file for server
"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # HUB_ADDR = os.environ.get('HUB_ADDR', 'api.uniduc.com')
    HUB_ADDR = os.environ.get('HUB_ADDR', 'localhost')
    # ROBOT -> 120807
    HUB_PORT = int(os.environ.get('HUB_PORT') or 120807)
    ADMIN_USER = os.environ.get('ADMIN_USER')  # Must be set in environment
    ADMIN_PWD = os.environ.get('ADMIN_PWD')  # Must be set in environment

    @staticmethod
    def init_app(app):
        pass


class DevConfig(Config):
    DEBUG = True
    ADMIN_USER = os.environ.get('ADMIN_USER', 'root')
    ADMIN_PWD = os.environ.get('ADMIN_PWD', 'toor')


class TestConfig(Config):
    TESTING = True
    ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
    ADMIN_PWD = os.environ.get('ADMIN_PWD', 'admin')


class Productionconfig(Config):
    OPTIMIZE = True


config = {
    'dev': DevConfig,
    'test': TestConfig,
    'production': Productionconfig,
    'default': DevConfig,
}
