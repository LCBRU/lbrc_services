import random
import string
from datetime import datetime
from lbrc_flask import db
from flask_security import UserMixin, RoleMixin


class Role(db.Model, RoleMixin):
    ADMIN_ROLENAME = "admin"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __str__(self):
        return self.name or ""


roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id")),
)


def random_password():
    return "".join(
        random.SystemRandom().choice(
            string.ascii_lowercase
            + string.ascii_uppercase
            + string.digits
            + string.punctuation
        )
        for _ in range(15)
    )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255), nullable=False, default=random_password)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(50))
    current_login_ip = db.Column(db.String(50))
    login_count = db.Column(db.Integer())
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    roles = db.relationship(
        "Role", secondary=roles_users, backref=db.backref("users", lazy="dynamic")
    )

    @property
    def is_admin(self):
        return self.has_role(Role.ADMIN_ROLENAME)

    @property
    def full_name(self):
        full_name = " ".join(filter(None, [self.first_name, self.last_name]))

        return full_name or self.email

    def __str__(self):
        return self.email
