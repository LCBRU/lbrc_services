from wtforms import validators
from lbrc_services.model.quotes import QuoteRequirementType, QuoteWorkLineNameSuggestion
from lbrc_services.model.services import Organisation, Service, User
from lbrc_flask.admin import init_admin as flask_init_admin, AdminCustomView
from lbrc_flask.forms.dynamic import FieldGroup, Field
from lbrc_flask.database import db
from flask_admin.model.form import InlineFormAdmin
from flask_admin.form.rules import BaseRule
from markupsafe import Markup
from flask import url_for


class ServiceView(AdminCustomView):

    form_args = dict(
        name=dict(validators=[validators.DataRequired()]),
        field_group=dict(query_factory=lambda: FieldGroup.query.order_by(FieldGroup.name)),
        owners=dict(query_factory=lambda: User.query.order_by(User.last_name, User.first_name, User.email)),
        excluded_organisations=dict(query_factory=lambda: Organisation.query.order_by(Organisation.name)),
    )
    column_list = [
        Service.name,
        "field_group",
        "owners",
    ]
    form_columns = [
        Service.name,
        Service.description,
        Service.introduction,
        "field_group",
        "owners",
        "excluded_organisations",
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


class QuoteRequirementTypeView(AdminCustomView):

    column_searchable_list = column_list = [
        QuoteRequirementType.name,
        QuoteRequirementType.description,
        QuoteRequirementType.importance,
    ]
    form_columns = [
        QuoteRequirementType.name,
        QuoteRequirementType.description,
        QuoteRequirementType.importance,
    ]


class QuoteWorkLineNameSuggestionView(AdminCustomView):

    column_searchable_list = column_list = [
        QuoteWorkLineNameSuggestion.name,
    ]
    form_columns = [
        QuoteWorkLineNameSuggestion.name,
    ]


class Link(BaseRule):
    def __init__(self, endpoint, attribute, text):
        super(Link, self).__init__()
        self.endpoint = endpoint
        self.text = text
        self.attribute = attribute

    def __call__(self, form, form_opts=None, field_args=None):
        if not field_args:
            field_args = {}

        _id = getattr(form._obj, self.attribute, None)

        if _id:
            return Markup('<a href="{url}">{text}</a>'.format(url=url_for(self.endpoint, id=_id), text=self.text))


class MultiLink(BaseRule):
    def __init__(self, endpoint, relation, id_attribute, name_attribute, order_attribute):
        super(MultiLink, self).__init__()
        self.endpoint = endpoint
        self.relation = relation
        self.id_attribute = id_attribute
        self.name_attribute = name_attribute
        self.order_attribute = order_attribute

    def __call__(self, form, form_opts=None, field_args=None):
        if not field_args:
            field_args = {}
        links = []

        for obj in getattr(form._obj, self.relation):
            id = getattr(obj, self.id_attribute, None)
            name = getattr(obj, self.name_attribute, 'Child')
            links.append(f'<a href="{url_for(self.endpoint, id=id)}">Edit Field "{name}"</a>')

        return Markup('<br>'.join(links))


class FieldlineView(InlineFormAdmin):
    form_edit_rules = (
        'name',
        Link(endpoint='field.edit_view', attribute='id', text="Hello"),
    )

class FieldGroupView(AdminCustomView):
    form_excluded_columns = ['fields']
    form_edit_rules = (
        'name',
        MultiLink(endpoint='field.edit_view', relation='fields', id_attribute='id', name_attribute="field_name", order_attribute="order"),
    )

class FieldView(AdminCustomView):
    column_filters = ['field_group']


def init_admin(app, title):
    flask_init_admin(
        app,
        title,
        [
            ServiceView(Service, db.session),
            FieldGroupView(FieldGroup, db.session),
            FieldView(Field, db.session),
            UserView(User, db.session),
            OrganisationView(Organisation, db.session),
            QuoteRequirementTypeView(QuoteRequirementType, db.session),
            QuoteWorkLineNameSuggestionView(QuoteWorkLineNameSuggestion, db.session),
        ],
    )
