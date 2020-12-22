import uuid
import pathlib
from flask import current_app
from flask.globals import request
from sqlalchemy.orm import backref
from werkzeug.utils import secure_filename
from lbrc_flask.database import db
from lbrc_flask.security import User as BaseUser, AuditMixin
from lbrc_flask.forms.dynamic import Field, FieldGroup


request_types_owners = db.Table(
    "request_types_owners",
    db.Column("request_type_id", db.Integer(), db.ForeignKey("request_type.id")),
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
)


class User(BaseUser):
    __table_args__ = {'extend_existing': True}

    owned_request_types = db.relationship("RequestType", secondary=request_types_owners)


class RequestType(AuditMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    field_group_id = db.Column(db.Integer, db.ForeignKey(FieldGroup.id))
    field_group = db.relationship(FieldGroup)
    owners = db.relationship(User, secondary=request_types_owners)

    def __str__(self):
        return self.name

    def get_field_for_field_name(self, field_name):
        if self.field_group:
            return self.field_group.get_field_for_field_name(field_name)


class RequestStatusType(db.Model):

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
    def get_request_status(cls, name):
        return RequestStatusType.query.filter_by(name=name).one()

    @classmethod
    def get_created(cls):
        return cls.get_request_status(RequestStatusType.CREATED)

    @classmethod
    def get_created_id(cls):
        return cls.get_created().id

    @classmethod
    def get_in_progress(cls):
        return cls.get_request_status(RequestStatusType.IN_PROGRESS)

    @classmethod
    def get_done(cls):
        return cls.get_request_status(RequestStatusType.DONE)

    @classmethod
    def get_awaiting_information(cls):
        return cls.get_request_status(RequestStatusType.AWAITING_INFORMATION)

    @classmethod
    def get_cancelled(cls):
        return cls.get_request_status(RequestStatusType.CANCELLED)

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    is_complete = db.Column(db.Boolean)
    is_active = db.Column(db.Boolean)


class Request(AuditMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    request_type_id = db.Column(db.Integer, db.ForeignKey(RequestType.id))
    request_type = db.relationship(RequestType, backref='requests')
    requestor_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    requestor = db.relationship(User, backref='requests', foreign_keys=[requestor_id])
    current_status_type_id = db.Column(db.Integer, db.ForeignKey(RequestStatusType.id), nullable=False)
    current_status_type = db.relationship(RequestStatusType)


class RequestStatus(AuditMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey(Request.id), nullable=False)
    request = db.relationship(Request, backref="status_history")
    notes = db.Column(db.String(255))
    request_status_type_id = db.Column(db.Integer, db.ForeignKey(RequestStatusType.id), nullable=False)
    request_status_type = db.relationship(RequestStatusType)


class RequestData(AuditMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    value = db.Column(db.UnicodeText())
    request_id = db.Column(db.Integer, db.ForeignKey(Request.id))
    request = db.relationship(Request, backref='data')
    field_id = db.Column(db.Integer, db.ForeignKey(Field.id))
    field = db.relationship(Field)

    @property
    def formated_value(self):
        return self.field.format_value(self.value)


class RequestFile(AuditMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    filename = db.Column(db.UnicodeText())
    local_filepath = db.Column(db.UnicodeText())
    request_id = db.Column(db.Integer, db.ForeignKey(Request.id))
    request = db.relationship(Request, backref='files')
    field_id = db.Column(db.Integer, db.ForeignKey(Field.id))
    field = db.relationship(Field)

    def set_filename_and_save(self, file):
        self.filename = file.filename

        local_filepath = self._new_local_filepath(
            filename=file.filename,
            parent=str(self.request.id),
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


def init_model(app):
    
    @app.before_first_request
    def request_status_type_setup():
        for name, details in RequestStatusType.all_details.items():
            if RequestStatusType.query.filter(RequestStatusType.name == name).count() == 0:
                db.session.add(
                    RequestStatusType(
                        name=name,
                        is_complete=details['is_complete'],
                        is_active=details['is_active'],
                    )
                )

        db.session.commit()
