from lbrc_flask.admin import init_admin as flask_init_admin
from lbrc_flask.forms.dynamic import get_dynamic_forms_admin_forms


def init_admin(app, title):
    flask_init_admin(
        app,
        title,
        get_dynamic_forms_admin_forms(),
    )
