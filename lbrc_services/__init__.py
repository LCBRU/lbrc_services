from lbrc_services.model.security import ROLE_QUOTER
from lbrc_services.model.services import User
from flask import Flask
from lbrc_flask import init_lbrc_flask
from lbrc_flask.security import init_security, Role
from lbrc_flask.forms.dynamic import init_dynamic_forms
from config import Config
from .ui import blueprint as ui_blueprint
from .admin import init_admin
from .model import init_model


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    TITLE = 'Requests'

    with app.app_context():
        init_lbrc_flask(app, TITLE)
        init_security(app, user_class=User, role_class=Role, roles=[ROLE_QUOTER])
        init_admin(app, TITLE)
        init_dynamic_forms(app)
        init_model(app)

    app.register_blueprint(ui_blueprint)

    return app
