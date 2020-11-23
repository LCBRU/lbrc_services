"""BRC Study Data Upload Site
"""
from flask import Flask
from .ui import blueprint as ui_blueprint
from lbrc_flask import init_lbrc_flask
from config import BaseConfig


def create_app(config=BaseConfig):
    """ Used to create flask application"""
    app = Flask(__name__)
    app.config.from_object(config)

    with app.app_context():
        init_lbrc_flask(app, 'Requests')

    app.register_blueprint(ui_blueprint)

    return app
