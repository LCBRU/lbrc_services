import string
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.forms import (
    EqualTo,
    password_length,
    password_required,
    get_form_field_label,
    ValidatorMixin,
    Form,
    PasswordFormMixin,
)
from flask_security.utils import verify_and_update_password, get_message
from flask_login import current_user
from wtforms.validators import ValidationError
from wtforms import PasswordField, SubmitField
from lbrc_requests.model import User, Role
from lbrc_flask import db


class PasswordPolicy(ValidatorMixin):
    def __init__(
        self,
        message=u"The password must contain a lowercase, "
        "uppercase and punctuation character",
    ):
        self.message = message

    def __call__(self, form, field):
        value = set(field.data)

        if (
            value.isdisjoint(string.ascii_lowercase)
            or value.isdisjoint(string.ascii_uppercase)
            or value.isdisjoint(string.punctuation)
        ):
            raise ValidationError(self.message)


class NewPasswordFormMixin:
    password = PasswordField(
        get_form_field_label("password"),
        validators=[password_required, password_length, PasswordPolicy()],
    )


class PasswordConfirmFormMixin:
    password_confirm = PasswordField(
        get_form_field_label("retype_password"),
        validators=[
            EqualTo("password", message="RETYPE_PASSWORD_MISMATCH"),
            password_required,
        ],
    )


class ResetPasswordForm(Form, NewPasswordFormMixin, PasswordConfirmFormMixin):
    """The default reset password form"""

    submit = SubmitField(get_form_field_label("reset_password"))


class ChangePasswordForm(Form, PasswordFormMixin):
    """The default change password form"""

    new_password = PasswordField(
        get_form_field_label("new_password"),
        validators=[password_required, password_length, PasswordPolicy()],
    )

    new_password_confirm = PasswordField(
        get_form_field_label("retype_password"),
        validators=[
            EqualTo("new_password", message="RETYPE_PASSWORD_MISMATCH"),
            password_required,
        ],
    )

    submit = SubmitField(get_form_field_label("change_password"))

    def validate(self):
        if not super(ChangePasswordForm, self).validate():
            return False

        if not verify_and_update_password(self.password.data, current_user):
            self.password.errors.append(get_message("INVALID_PASSWORD")[0])
            return False
        if self.password.data.strip() == self.new_password.data.strip():
            self.password.errors.append(get_message("PASSWORD_IS_THE_SAME")[0])
            return False
        return True


def init_security(app):
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(
        app,
        user_datastore,
        reset_password_form=ResetPasswordForm,
        change_password_form=ChangePasswordForm,
    )

    @app.before_first_request
    def init_security():
        admin_role = user_datastore.find_or_create_role(
            name=Role.ADMIN_ROLENAME, description="Administration"
        )

        for a in app.config["ADMIN_EMAIL_ADDRESSES"].split(";"):
            if not user_datastore.find_user(email=a):
                print('Creating administrator "{}"'.format(a))
                user = user_datastore.create_user(email=a)
                user_datastore.add_role_to_user(user, admin_role)

        db.session.commit()
