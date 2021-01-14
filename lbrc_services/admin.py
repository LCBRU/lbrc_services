from wtforms import validators
from lbrc_requests.model import RequestType, User
from lbrc_flask.admin import init_admin as flask_init_admin, AdminCustomView
from lbrc_flask.forms.dynamic import FieldGroup, get_dynamic_forms_admin_forms
from lbrc_flask.database import db


class RequestTypeView(AdminCustomView):

    form_args = dict(
        name=dict(validators=[validators.DataRequired()]),
        field_group=dict(query_factory=lambda: FieldGroup.query.order_by(FieldGroup.name)),
        owners=dict(query_factory=lambda: User.query.order_by(User.last_name, User.first_name, User.email)),
    )
    form_columns = [
        RequestType.name,
        "field_group",
        "owners",
    ]
    column_searchable_list = [RequestType.name]


def init_admin(app, title):
    flask_init_admin(
        app,
        title,
        [
            RequestTypeView(RequestType, db.session),
            *get_dynamic_forms_admin_forms(),
        ],
    )
