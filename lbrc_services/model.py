import uuid
import pathlib
from flask import current_app
from werkzeug.utils import secure_filename
from lbrc_flask.database import db
from lbrc_flask.security import User as BaseUser, AuditMixin
from lbrc_flask.forms.dynamic import Field, FieldGroup


services_owners = db.Table(
    "services_owners",
    db.Column("service_id", db.Integer(), db.ForeignKey("service.id")),
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
)


class User(BaseUser):
    __table_args__ = {'extend_existing': True}

    owned_services = db.relationship("Service", secondary=services_owners)


class Service(AuditMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    field_group_id = db.Column(db.Integer, db.ForeignKey(FieldGroup.id))
    field_group = db.relationship(FieldGroup)
    owners = db.relationship(User, secondary=services_owners)

    def __str__(self):
        return self.name

    def get_field_for_field_name(self, field_name):
        if self.field_group:
            return self.field_group.get_field_for_field_name(field_name)


class TaskStatusType(db.Model):

    CREATED = 'Created'
    IN_PROGRESS = 'In Progress'
    DONE = 'Done'
    AWAITING_INFORMATION = 'Awaiting Information'
    CANCELLED = 'Cancelled'

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

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    is_complete = db.Column(db.Boolean)
    is_active = db.Column(db.Boolean)


class Task(AuditMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    service_id = db.Column(db.Integer, db.ForeignKey(Service.id))
    service = db.relationship(Service, backref='tasks')
    requestor_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    requestor = db.relationship(User, backref='tasks', foreign_keys=[requestor_id])
    current_status_type_id = db.Column(db.Integer, db.ForeignKey(TaskStatusType.id), nullable=False)
    current_status_type = db.relationship(TaskStatusType)

    @property
    def total_todos(self):
        return len(self.todos)

    @property
    def required_todos(self):
        return len([t for t in self.todos if t.is_required])

    @property
    def complete_todos(self):
        return len([t for t in self.todos if t.is_complete])


class TaskStatus(AuditMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id), nullable=False)
    task = db.relationship(Task, backref="status_history")
    notes = db.Column(db.String(255))
    task_status_type_id = db.Column(db.Integer, db.ForeignKey(TaskStatusType.id), nullable=False)
    task_status_type = db.relationship(TaskStatusType)


class TaskData(AuditMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    value = db.Column(db.UnicodeText())
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id))
    task = db.relationship(Task, backref='data')
    field_id = db.Column(db.Integer, db.ForeignKey(Field.id))
    field = db.relationship(Field)

    @property
    def formated_value(self):
        return self.field.format_value(self.value)


class TaskFile(AuditMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    filename = db.Column(db.UnicodeText())
    local_filepath = db.Column(db.UnicodeText())
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id))
    task = db.relationship(Task, backref='files')
    field_id = db.Column(db.Integer, db.ForeignKey(Field.id))
    field = db.relationship(Field)

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


class ToDo(AuditMixin, db.Model):

    OUTSTANDING = 'Outstanding'
    COMPLETED = 'Completed'
    NOT_REQUIRED = 'Not Required'

    id = db.Column(db.Integer(), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey(Task.id))
    task = db.relationship(Task, backref='todos')
    description = db.Column(db.UnicodeText())
    status = db.Column(db.Integer, db.CheckConstraint("status IN (-1, 0, 1)"), nullable=False, default=0)

    @property
    def status_name(self):
        return {
            -1: ToDo.NOT_REQUIRED,
            0: ToDo.OUTSTANDING,
            1: ToDo.COMPLETED,
        }[self.status]

    @property
    def is_outstanding(self):
        return self.status == 0

    @property
    def is_required(self):
        return self.status > -1

    @property
    def is_complete(self):
        return self.status == 1


def init_model(app):
    
    @app.before_first_request
    def task_status_type_setup():
        for name, details in TaskStatusType.all_details.items():
            if TaskStatusType.query.filter(TaskStatusType.name == name).count() == 0:
                db.session.add(
                    TaskStatusType(
                        name=name,
                        is_complete=details['is_complete'],
                        is_active=details['is_active'],
                    )
                )

        db.session.commit()
