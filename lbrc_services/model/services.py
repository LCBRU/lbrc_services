import uuid
import pathlib
import re
from flask import current_app
from sqlalchemy.orm import backref
from werkzeug.utils import secure_filename
from lbrc_flask.database import db
from lbrc_flask.security import User as BaseUser, AuditMixin
from lbrc_flask.forms.dynamic import Field, FieldGroup
from lbrc_flask.model import CommonMixin


services_owners = db.Table(
    "services_owners",
    db.Column("service_id", db.Integer(), db.ForeignKey("service.id")),
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
)


tasks_organisations = db.Table(
    "tasks_organisations",
    db.Column("task_id", db.Integer(), db.ForeignKey("task.id")),
    db.Column("organisation_id", db.Integer(), db.ForeignKey("organisation.id")),
)


class User(BaseUser):
    __table_args__ = {'extend_existing': True}

    owned_services = db.relationship("Service", lazy="joined", secondary=services_owners, backref='owners')

    @property
    def service_owner(self):
        return len(self.owned_services) > 0


class Service(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    generic_recipients = db.Column(db.String(255))
    suppress_owner_email = db.Column(db.Boolean)
    field_group_id = db.Column(db.Integer, db.ForeignKey(FieldGroup.id))
    field_group = db.relationship(FieldGroup)
    introduction = db.Column(db.UnicodeText())
    description = db.Column(db.UnicodeText())

    def __str__(self):
        return self.name

    def get_field_for_field_name(self, field_name):
        if self.field_group:
            return self.field_group.get_field_for_field_name(field_name)

    @property
    def notification_email_addresses(self):
        return list(filter(len, [r.email for r in self.owners if not self.suppress_owner_email] + re.split(r'[;,\s]+', self.generic_recipients or '')))


class TaskStatusType(db.Model, CommonMixin):

    CREATED = 'Created'
    IN_PROGRESS = 'In Progress'
    DONE = 'Done'
    AWAITING_INFORMATION = 'Awaiting Information'
    CANCELLED = 'Cancelled'
    DECLINED = 'Declined'
    DUPLICATE = 'Duplicate'

    all_details = {
        CREATED: {
            'is_complete': False,
            'is_active': False,
        },
        IN_PROGRESS: {
            'is_complete': False,
            'is_active': True,
        },
        DONE: {
            'is_complete': True,
            'is_active': False,
        },
        AWAITING_INFORMATION: {
            'is_complete': False,
            'is_active': False,
        },
        CANCELLED: {
            'is_complete': True,
            'is_active': False,
        },
        DECLINED: {
            'is_complete': True,
            'is_active': False,
        },
        DUPLICATE: {
            'is_complete': True,
            'is_active': False,
        },
    }

    @classmethod
    def get_task_status(cls, name):
        return TaskStatusType.query.filter_by(name=name).one()

    @classmethod
    def get_created(cls):
        return cls.get_task_status(TaskStatusType.CREATED)

    @classmethod
    def get_created_id(cls):
        return cls.get_created().id

    @classmethod
    def get_in_progress(cls):
        return cls.get_task_status(TaskStatusType.IN_PROGRESS)

    @classmethod
    def get_done(cls):
        return cls.get_task_status(TaskStatusType.DONE)

    @classmethod
    def get_awaiting_information(cls):
        return cls.get_task_status(TaskStatusType.AWAITING_INFORMATION)

    @classmethod
    def get_cancelled(cls):
        return cls.get_task_status(TaskStatusType.CANCELLED)

    @classmethod
    def get_declined(cls):
        return cls.get_task_status(TaskStatusType.DECLINED)

    @classmethod
    def get_duplicate(cls):
        return cls.get_task_status(TaskStatusType.DUPLICATE)

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    is_complete = db.Column(db.Boolean)
    is_active = db.Column(db.Boolean)


class Organisation(db.Model, CommonMixin):

    CARDIOVASCULAR = 'BRC Cardiovascular Theme'
    LIFESTYLE = 'BRC Lifestyle Theme'
    PRECICION = 'BRC Precision Medicine Theme'
    RESPIRATORY = 'BRC Respiratory Theme'
    LDC = 'Leicester Diabetes Centre'
    PRC = 'Patient Recruitment Centre'
    RandI = 'R&I'
    OTHER = 'Other - please specify'

    all_organisations = [CARDIOVASCULAR, LIFESTYLE, PRECICION, RESPIRATORY, LDC, PRC, RandI, OTHER]

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))

    @classmethod
    def get_organisation(cls, name):
        return Organisation.query.filter_by(name=name).one()

    @classmethod
    def get_other(cls):

        return cls.get_organisation(Organisation.OTHER)


class Task(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    organisation_description = db.Column(db.String(255))
    service_id = db.Column(db.Integer, db.ForeignKey(Service.id))
    service = db.relationship(Service, lazy="joined", backref='tasks')
    requestor_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    requestor = db.relationship(User, lazy="joined", backref='tasks', foreign_keys=[requestor_id])
    current_status_type_id = db.Column(db.Integer, db.ForeignKey(TaskStatusType.id), nullable=False)
    current_status_type = db.relationship(TaskStatusType)
    current_assigned_user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=True)
    current_assigned_user = db.relationship(User, foreign_keys=[current_assigned_user_id])

    organisations = db.relationship("Organisation", lazy="joined", secondary=tasks_organisations, backref='tasks')

    @property
    def long_name(self):
        return "{}: {}".format(self.service.name, self.name)

    @property
    def total_todos(self):
        return len(self.todos)

    @property
    def required_todos(self):
        return len([t for t in self.todos if t.is_required])

    @property
    def complete_todos(self):
        return len([t for t in self.todos if t.is_complete])

    @property
    def notification_email_addresses(self):
        return self.service.notification_email_addresses + [self.requestor.email]

    def get_data_for_task_id(self, field_id):
        return next((t for t in self.data if t.field_id == field_id), None)

    @property
    def completed_date(self):
        last_status = next((
            ts for ts in reversed(sorted(self.status_history, key=lambda sh: sh.created_date))
        ), None)

        if last_status and last_status.task_status_type.is_complete:
            return last_status.created_date


class TaskStatus(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id), nullable=False)
    task = db.relationship(Task, backref="status_history")
    notes = db.Column(db.String(255))
    task_status_type_id = db.Column(db.Integer, db.ForeignKey(TaskStatusType.id), nullable=False)
    task_status_type = db.relationship(TaskStatusType, backref="assigned_tasks")


class TaskAssignedUser(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id), nullable=False)
    task = db.relationship(Task, backref="assigned_user_history")
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User)
    notes = db.Column(db.String(255))


class TaskData(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    value = db.Column(db.UnicodeText())
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id))
    task = db.relationship(Task, backref=backref('data', cascade='all, delete-orphan'))
    field_id = db.Column(db.Integer, db.ForeignKey(Field.id))
    field = db.relationship(Field, lazy="joined")

    @property
    def formated_value(self):
        return self.field.format_value(self.value)

    @property
    def data_value(self):
        return self.field.data_value(self.value)


class TaskFile(AuditMixin, CommonMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    filename = db.Column(db.UnicodeText())
    local_filepath = db.Column(db.UnicodeText())
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id))
    task = db.relationship(Task, backref=backref('files', cascade='all, delete-orphan'))
    field_id = db.Column(db.Integer, db.ForeignKey(Field.id))
    field = db.relationship(Field, lazy="joined")

    def set_filename_and_save(self, file):
        self.filename = file.filename

        local_filepath = self._new_local_filepath(
            filename=file.filename,
            parent=str(self.task.id),
        )

        self.local_filepath = str(local_filepath)

        local_filepath.parent.mkdir(parents=True, exist_ok=True)
        file.save(local_filepath)

    def _new_local_filepath(self, filename, parent=None):
        result = pathlib.Path(current_app.config["FILE_UPLOAD_DIRECTORY"])

        if parent:
            result = result.joinpath(secure_filename(parent))

        result = result.joinpath(secure_filename("{}_{}".format(uuid.uuid1().hex, filename)))

        return result


class ToDo(AuditMixin, CommonMixin, db.Model):

    OUTSTANDING = 'Outstanding'
    COMPLETED = 'Completed'
    NOT_REQUIRED = 'Not Required'

    _status_map = {
        -1: NOT_REQUIRED,
        0: OUTSTANDING,
        1: COMPLETED,
    }

    @staticmethod
    def get_status_code_from_name(name):
        return {v: k for k, v in ToDo._status_map.items()}[name]

    id = db.Column(db.Integer(), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id))
    task = db.relationship(Task, backref='todos')
    description = db.Column(db.UnicodeText())
    status = db.Column(db.Integer, db.CheckConstraint("status IN (-1, 0, 1)"), nullable=False, default=0)

    @property
    def status_name(self):
        return ToDo._status_map[self.status]

    @property
    def is_outstanding(self):
        return self.status == 0

    @property
    def is_required(self):
        return self.status > -1

    @property
    def is_complete(self):
        return self.status == 1
