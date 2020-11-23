from flask import Flask
from .ui import blueprint as ui_blueprint
from lbrc_flask import init_lbrc_flask
from lbrc_flask.config import BaseConfig


def create_app(config=BaseConfig):
    app = Flask(__name__)
    app.config.from_object(config)

    with app.app_context():
        init_lbrc_flask(app, title='Requests')

    app.register_blueprint(ui_blueprint)

    return app
