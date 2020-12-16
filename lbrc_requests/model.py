import uuid
import pathlib
from flask import current_app
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


class Request(AuditMixin, db.Model):

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    request_type_id = db.Column(db.Integer, db.ForeignKey(RequestType.id))
    request_type = db.relationship(RequestType, backref='requests')
    requestor_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    requestor = db.relationship(User, backref='requests', foreign_keys=[requestor_id])


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

    def store_file(self, file):
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
