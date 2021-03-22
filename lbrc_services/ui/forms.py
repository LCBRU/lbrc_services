from lbrc_flask.forms import SearchForm, FlashingForm
from flask_login import current_user
from lbrc_flask.forms.dynamic import FormBuilder
from lbrc_flask.security import current_user_id
from wtforms import SelectField, TextAreaField, StringField
from wtforms.fields.simple import HiddenField
from wtforms.validators import DataRequired, Length, ValidationError
from lbrc_services.model import TaskStatusType, Service, Task, Organisation, User


def _get_requestor_choices():
    service_ids = Service.query.with_entities(Service.id.distinct()).join(Service.owners).filter(User.id == current_user.id)
    requestor_ids = Task.query.with_entities(Task.requestor_id.distinct()).filter(Task.service_id.in_(service_ids))
    submitters = sorted(User.query.filter(User.id.in_(requestor_ids)).all(), key=lambda u: u.full_name)

    return [(0, 'All')] + [(u.id, u.full_name) for u in submitters]


def _get_service_choices():
    services = Service.query.join(Service.owners).filter(User.id == current_user.id).all()

    return [(0, 'All')] + [(rt.id, rt.name) for rt in services]


def _get_task_status_type_choices():
    task_status_types = TaskStatusType.query.order_by(TaskStatusType.name.asc()).all()
    return [(rt.id, rt.name) for rt in task_status_types]


def _get_combined_task_status_type_choices():
    return [(0, 'Outstanding (not done, declined or cancelled)'), (-1, 'Completed (done, declined or cancelled)'), (-2, 'All')] + _get_task_status_type_choices()


class TaskSearchForm(SearchForm):
    service_id = SelectField('Service', coerce=int, choices=[])
    task_status_type_id = SelectField('Status', coerce=int, choices=[])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.service_id.choices = _get_service_choices()
        self.task_status_type_id.choices = _get_combined_task_status_type_choices()


class MyJobsSearchForm(TaskSearchForm):
    requestor_id = SelectField('Requesterd By', coerce=int, choices=[])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.requestor_id.choices = _get_requestor_choices()


class TaskUpdateStatusForm(FlashingForm):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.status.choices = _get_task_status_type_choices()

    task_id = HiddenField()
    status = SelectField("New Status", validators=[DataRequired()])
    notes = TextAreaField("Notes", validators=[Length(max=500)])


class EditToDoForm(FlashingForm):
    task_id = HiddenField()
    todo_id = HiddenField()
    description = TextAreaField("Description", validators=[Length(max=500)])


def _get_organisation_choices():
    orgs = Organisation.query.order_by(Organisation.name.asc()).all()

    return [('', '')] + [(t.id, t.name) for t in orgs]

def required_when_other_organisation(form, field):
    if field.data and (not isinstance(field.data, str) or field.data.strip()):
        return

    if not form.organisation_id.data:
        return
    
    if not form.organisation_id.data.isnumeric():
        return

    if int(form.organisation_id.data) == Organisation.get_other().id:
        raise ValidationError('This field is required.')


def get_create_task_form(service, task=None):
    users = User.query.order_by(User.last_name.asc(), User.first_name.asc()).all()
    requestor_choices = [('', '')] + [(t.id, t.full_name) for t in users]

    builder = FormBuilder()
    builder.add_form_field('requestor_id', SelectField('Requesting User', default=current_user_id, choices=requestor_choices, validators=[DataRequired()]))
    builder.add_form_field('name', StringField('Name', validators=[Length(max=255), DataRequired()]))
    builder.add_form_field('organisation_id', SelectField('Organisation', choices=_get_organisation_choices(), validators=[DataRequired()]))
    builder.add_form_field('organisation_description', StringField('Organisation Description', validators=[Length(max=255), required_when_other_organisation]))
    builder.add_field_group(service.field_group)

    class DynamicTask:
        pass

    dt = DynamicTask()

    if task is not None:
        dt.id = task.id
        dt.name = task.name
        dt.organisation_id = task.organisation_id
        dt.organisation_description = task.organisation_description

        for td in task.data:
            setattr(dt, td.field.field_name, td.data_value)

    result = builder.get_form()(obj=dt)

    return result
