"""BRC Study Data Upload Site
"""
import os
import traceback
from flask import Flask
from .ui import blueprint as ui_blueprint
from lbrc_flask import init_lbrc_flask
from lbrc_requests.security import init_security
from config import BaseConfig


def create_app(config=BaseConfig):
    """ Used to create flask application"""
    app = Flask(__name__)
    app.config.from_object(config)

    with app.app_context():
        init_lbrc_flask(app, 'Requests')
        init_security(app)

    app.register_blueprint(ui_blueprint)

    return app
