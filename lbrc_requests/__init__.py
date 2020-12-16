from lbrc_requests.model import User
from flask import Flask
from lbrc_flask import init_lbrc_flask
from lbrc_flask.security import init_security, Role
from lbrc_flask.forms.dynamic import init_dynamic_forms
from config import Config
from .ui import blueprint as ui_blueprint
from .admin import init_admin


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    TITLE = 'Requests'

    with app.app_context():
        init_lbrc_flask(app, TITLE)
        init_security(app, user_class=User, role_class=Role)
        init_admin(app, TITLE)
        init_dynamic_forms(app)

    app.register_blueprint(ui_blueprint)

    return app
