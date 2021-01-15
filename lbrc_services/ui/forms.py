from lbrc_flask.forms import SearchForm, FlashingForm
from flask_login import current_user
from wtforms import SelectField, TextAreaField
from wtforms.fields.simple import HiddenField
from wtforms.validators import DataRequired, Length
from lbrc_services.model import TaskStatusType, Service, Task, User


def _get_requestor_choices():
    service_ids = Service.query.with_entities(Service.id.distinct()).join(Service.owners).filter(User.id == current_user.id).subquery()
    requestor_ids = Task.query.with_entities(Task.requestor_id.distinct()).filter(Task.service_id.in_(service_ids)).subquery()
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
