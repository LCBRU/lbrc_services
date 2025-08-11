from operator import or_
from flask import url_for
from lbrc_flask.forms import SearchForm, FlashingForm
from flask_login import current_user
from itertools import groupby
from lbrc_flask.forms.dynamic import Field, FormBuilder
from lbrc_flask.security import current_user_id
from lbrc_flask.security.ldap import get_or_create_ldap_user
from lbrc_flask.database import db
from sqlalchemy import select
from wtforms import SelectField, TextAreaField, StringField, SelectMultipleField
from wtforms.fields import DateField
from wtforms.fields.simple import HiddenField
from wtforms.validators import DataRequired, Length, ValidationError
from lbrc_services.model.quotes import QuotePricingType, QuoteStatusType
from lbrc_services.model.services import TaskStatusType, Service, Task, Organisation, User
from sqlalchemy.orm import aliased


def _get_requestor_choices(add_all=True):
    service_ids = Service.query.with_entities(Service.id.distinct()).join(Service.owners).filter(User.id == current_user.id)
    requestor_ids = Task.query.with_entities(Task.requestor_id.distinct()).filter(Task.service_id.in_(service_ids))
    submitters = sorted(User.query.filter(User.id.in_(requestor_ids)).all(), key=lambda u: u.full_name)

    result = [(u.id, u.full_name) for u in submitters]

    if add_all:
        result = [(0, 'All')] + result

    return result


def _get_service_choices():
    services = Service.query.join(Service.owners).filter(User.id == current_user.id).all()

    return [(0, 'All')] + [(rt.id, rt.name) for rt in services]


def _get_organisation_search_choices():
    organisations = Organisation.query.all()

    return [(0, 'All')] + [(rt.id, rt.name) for rt in organisations]


def _get_task_status_type_choices():
    task_status_types = TaskStatusType.query.order_by(TaskStatusType.name.asc()).all()
    return [(rt.id, rt.name) for rt in task_status_types]


def _owners_of_my_services():
    owner = aliased(User)
    current = aliased(User)

    return db.session.execute(
        select(owner)
        .join(owner.owned_services)
        .join(current, Service.owners)
        .where(current.id == current_user_id())
        .where(owner.id != current_user_id())
    ).unique().scalars()


def _get_task_assigned_user_choices():
    return [(0, 'Unassigned')] + [(o.id, o.full_name) for o in _owners_of_my_services()]


def _get_task_choices():
    q = select(Task)
    q = q.where(or_(
        Task.current_assigned_user_id == 0,
        or_(
            Task.current_assigned_user_id == None,
            Task.current_assigned_user_id == current_user_id(),
        )
    ))
    q = q.where(Task.todos.any())

    return [(0, 'All')] + [(t.id, t.name) for t in db.session.execute(q).unique().scalars()]


def _get_service_assigned_user_choices(service_id):
    service = db.get_or_404(Service, service_id)
    return [(0, 'Unassigned')] + [(o.id, o.full_name) for o in service.owners]


def _get_task_assigned_user_search_choices():
    return [
        (-3, 'Mine and Unassigned'),
        (-2, 'Mine'),
        (-1, 'All'),
        (0, 'Unassigned')] + [(o.id, o.full_name) for o in _owners_of_my_services()]


def _get_combined_task_status_type_choices():
    return [
        (0, 'Open (created, in progress or awaiting information)'),
        (-1, 'Open or recently closed'),
        (-2, 'Closed (done, declined or cancelled)'),
        (-3, 'All')] + _get_task_status_type_choices()


def _get_quote_status_type_choices():
    quote_status_types = QuoteStatusType.query.order_by(QuoteStatusType.name.asc()).all()
    return [(rt.id, rt.name) for rt in quote_status_types]


def _get_combined_quote_status_type_choices():
    return [(0, 'Open (draft, awaiting approval, issued, due or charged)'), (-1, 'Closed (paid, deleted or duplicate)'), (-2, 'All')] + _get_quote_status_type_choices()


def _get_report_grouper_choices():
    field_group_ids = Service.query.with_entities(Service.field_group_id.distinct()).join(Service.owners).filter(User.id == current_user.id)
    report_group_fields = Field.query.filter(Field.field_group_id.in_(field_group_ids)).filter(Field.reportable == True).all()

    return [(-3, 'Requested Month'), (-2, 'Current Status'), (-1, 'Organisation')] + sorted([(f.id, '{}: {}'.format(f.field_group.name, f.get_label())) for f in report_group_fields], key=lambda x: x[1])


class QuoteSearchForm(SearchForm):
    created_date_from = DateField('Quote Created From', format='%Y-%m-%d')
    created_date_to = DateField('Quote Created To', format='%Y-%m-%d')
    organisation_id = SelectField('Organisation', coerce=int, choices=[], default=0)
    quote_status_type_id = SelectField('Status', coerce=int, choices=[])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.quote_status_type_id.choices = _get_combined_quote_status_type_choices()
        self.organisation_id.choices = _get_organisation_search_choices()


class TodoSearchForm(SearchForm):
    task_id = SelectField('Job', coerce=int, choices=[])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.task_id.choices = _get_task_choices()


class TaskSearchForm(SearchForm):
    created_date_from = DateField('Request Made From', format='%Y-%m-%d')
    created_date_to = DateField('Request Made To', format='%Y-%m-%d')
    service_id = SelectField('Service', coerce=int, choices=[])
    organisation_id = SelectField('Organisation', coerce=int, choices=[], default=0)
    task_status_type_id = SelectField('Status', coerce=int, choices=[])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.service_id.choices = _get_service_choices()
        self.task_status_type_id.choices = _get_combined_task_status_type_choices()
        self.organisation_id.choices = _get_organisation_search_choices()


class MyJobsSearchForm(TaskSearchForm):
    requestor_id = SelectField('Requesterd By', coerce=int, choices=[], render_kw={'class': 'select2 form-control'})
    assigned_user_id = SelectField('Assigned User', coerce=int, choices=[], default=-3)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.requestor_id.choices = _get_requestor_choices()
        self.assigned_user_id.choices = _get_task_assigned_user_search_choices()


class ReportSearchForm(MyJobsSearchForm):
    report_grouper_id = SelectField('Job Count By...', coerce=int, choices=[], default=-3)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.report_grouper_id.choices = _get_report_grouper_choices()


class TaskUpdateAssignedUserForm(FlashingForm):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.assigned_user.choices = _get_task_assigned_user_choices()

    assigned_user = SelectField("Assigned User", validators=[DataRequired()])
    notes = TextAreaField("Notes", validators=[Length(max=255)])


class TaskUpdateStatusForm(FlashingForm):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.status.choices = _get_task_status_type_choices()

    task_id = HiddenField()
    status = SelectField("New Status", validators=[DataRequired()])
    notes = TextAreaField("Notes", validators=[Length(max=255)])


class EditToDoForm(FlashingForm):
    description = TextAreaField("Description", validators=[Length(max=500)])


def _get_organisation_choices(service=None):
    q = select(Organisation).order_by(Organisation.name.asc())

    if service:
        q = q.where(~Organisation.excluded_services.any(Service.id == service.id))

    return [(str(t.id), t.name) for t in db.session.execute(q).scalars()]


def required_when_other_organisation(form, field):
    if field.data and (not isinstance(field.data, str) or field.data.strip()):
        return

    if form.__contains__('organisations'):
        if any(int(oid) == Organisation.get_other().id for oid in form.organisations.data):
            raise ValidationError('This field is required.')
    elif form.__contains__('organisation_id') and (form.organisation_id.data or '').isnumeric():
        if int(form.organisation_id.data) == Organisation.get_other().id:
            raise ValidationError('This field is required.')



def _user_coerce(value):
    if str(value).isnumeric():
        return value

    u = User.query.filter(User.username == value).one_or_none()

    if u:
        return u.id

    u = get_or_create_ldap_user(value)

    if u:
        return u.id
    
    return None


class QuoteUpdateForm(FlashingForm):
    quote_id = HiddenField()
    requestor_id = SelectField(
        'Requesting User',
        coerce=_user_coerce,
        default=current_user_id,
        validate_choice=False,
        validators=[DataRequired()],
        render_kw={
            'class':' select2',
        },
    )
    name = StringField('Quote Title', validators=[Length(max=255), DataRequired()])
    organisation_id = SelectField('Organisation', validators=[DataRequired()])
    organisation_description = StringField('Organisation Description', validators=[Length(max=255), required_when_other_organisation])
    quote_pricing_type_id = SelectField('Pricing Type', validators=[DataRequired()])
    date_requested = DateField('Date Requested', validators=[DataRequired()])
    date_required = DateField('Date Required')
    introduction = TextAreaField('Introduction')
    conclusion = TextAreaField('Conclusion')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.requestor_id.render_kw['data-options-href'] = url_for('ui.user_search')
        self.organisation_id.choices = _get_organisation_choices()
        self.quote_pricing_type_id.choices = [(0, '')] + [(pt.id, pt.name) for pt in QuotePricingType.query.all()]


def get_create_task_form(service, task=None, is_pdf=False):
    builder = get_create_task_form_builder(service, is_pdf)
    result = populate_create_task_form(task, builder)

    return result


def get_create_task_form_builder(service, is_pdf):
    builder = FormBuilder()

    if is_pdf:
        add_task_user_fields_pdf(builder)
    else:
        add_task_user_fields(builder, service)

    builder.add_form_field('name', StringField('Request Title', validators=[Length(max=255), DataRequired()]))
    builder.add_form_field('organisations', SelectMultipleField('Organisations', choices=_get_organisation_choices(service), validators=[DataRequired()]))
    builder.add_form_field('organisation_description', StringField('Organisation Description', validators=[Length(max=255), required_when_other_organisation]))
    builder.add_field_group(service.field_group)

    return builder


def add_task_user_fields(builder, service):
    users = User.query.order_by(User.last_name.asc(), User.first_name.asc()).all()
    requestor_choices = [('', '')] + [(t.id, t.full_name) for t in users]

    default_assigned_user_id = None

    if current_user in service.owners:
        default_assigned_user_id = current_user_id

    builder.add_form_field('requestor_id', SelectField(
        'Requestor',
        coerce=_user_coerce,
        default=current_user_id,
        choices=requestor_choices,
        validate_choice=False,
        validators=[DataRequired()],
    ))
    builder.add_form_field('assigned_user_id', SelectField(
        'Assigned User',
        coerce=_user_coerce,
        default=default_assigned_user_id,
        choices=_get_service_assigned_user_choices(service.id),
        validate_choice=False,
    ))


def add_task_user_fields_pdf(builder):
    builder.add_form_field('requestor_id', StringField('Requestor'))


def populate_create_task_form(task, builder):
    class DynamicTask:
        pass

    dt = DynamicTask()

    if task is not None:
        dt.id = task.id
        dt.name = task.name
        dt.organisations = [str(o.id) for o in task.organisations]
        dt.organisation_description = task.organisation_description

        for field, data in groupby(task.data, lambda d: d.field):
            if field.field_type.is_select_multiple:
                setattr(dt, field.field_name, [d.data_value for d in data])
            else:
                setattr(dt, field.field_name, next(data).data_value)

    result = builder.get_form()(obj=dt)

    return result
