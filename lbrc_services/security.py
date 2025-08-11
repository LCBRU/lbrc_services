from lbrc_flask.security import init_roles, init_users
from lbrc_services.model.security import get_roles

def init_authorization():
    init_roles(get_roles())
    init_users()
