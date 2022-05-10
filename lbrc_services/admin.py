from wtforms import validators
from lbrc_services.model.services import Organisation, Service, User
from lbrc_flask.admin import init_admin as flask_init_admin, AdminCustomView
from lbrc_flask.forms.dynamic import FieldGroup, get_dynamic_forms_admin_forms
from lbrc_flask.database import db


class ServiceView(AdminCustomView):

    form_args = dict(
        name=dict(validators=[validators.DataRequired()]),
        field_group=dict(query_factory=lambda: FieldGroup.query.order_by(FieldGroup.name)),
        owners=dict(query_factory=lambda: User.query.order_by(User.last_name, User.first_name, User.email)),
    )
    column_list = [
        Service.name,
        "field_group",
        "owners",
    ]
    form_columns = [
        Service.name,
        Service.introduction,
        "field_group",
        "owners",
        Service.generic_recipients,
        Service.suppress_owner_email,
    ]
    column_searchable_list = [Service.name]


class UserView(AdminCustomView):

    column_searchable_list = column_list = [
        User.username,
        User.email,
        User.first_name,
        User.last_name,
        User.ldap_user,
        User.active,
    ]
    form_columns = [
        User.username,
        User.email,
        User.first_name,
        User.last_name,
        'roles',
        User.active,
    ]

class OrganisationView(AdminCustomView):

    column_searchable_list = column_list = [
        Organisation.name,
    ]
    form_columns = [
        Organisation.name,
    ]

def init_admin(app, title):
    flask_init_admin(
        app,
        title,
        [
            ServiceView(Service, db.session),
            *get_dynamic_forms_admin_forms(),
            UserView(User, db.session),
            OrganisationView(Organisation, db.session),
        ],
    )
