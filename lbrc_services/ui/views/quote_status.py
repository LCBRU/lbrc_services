from flask_security import roles_required
from flask import render_template, url_for
from flask_login import current_user
from lbrc_services.model.quotes import Quote, QuoteStatus, QuoteStatusType
from lbrc_flask.database import db
from lbrc_flask.security import get_users_for_role
from lbrc_flask.emailing import email
from lbrc_services.model.security import ROLE_QUOTE_CHARGER, ROLE_QUOTE_APPROVER, ROLE_QUOTER
from lbrc_flask.forms import FlashingForm
from wtforms import SelectField, TextAreaField
from wtforms.validators import DataRequired, Length

from lbrc_services.ui.forms import _get_quote_status_type_choices
from .. import blueprint
from lbrc_flask.response import refresh_response, REFRESH_DETAILS_TRIGGER


class QuoteUpdateStatusForm(FlashingForm):
    status_type_id = SelectField("New Status", validators=[DataRequired()])
    notes = TextAreaField("Notes", validators=[Length(max=255)])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.status_type_id.choices = _get_quote_status_type_choices()


@blueprint.route("/quote/<int:quote_id>/status/update", methods=["GET", "POST"])
@roles_required(ROLE_QUOTER)
def quote_status_update(quote_id):
    quote = db.get_or_404(Quote, quote_id)
   
    form = QuoteUpdateStatusForm()

    if form.validate_on_submit():
        status_type = db.get_or_404(QuoteStatusType, form.status_type_id.data)

        _update_quote_status(
            quote.id,
            status_type,
            form.notes.data,
        )
        return refresh_response()

    return render_template(
        "lbrc/form_modal.html",
        title=f"Amend Status for Quote '{quote.name}'",
        form=form,
        url=url_for('ui.quote_status_update', quote_id=quote.id),
        closing_events=[REFRESH_DETAILS_TRIGGER],
    )


def _update_quote_status(quote_id, new_quote_status_type, notes):
        quote = db.get_or_404(Quote, quote_id)

        quote_status = QuoteStatus(
            quote=quote,
            quote_status_type=new_quote_status_type,
            notes=notes,
        )

        db.session.add(quote_status)

        _send_quote_status_email(quote, new_quote_status_type)

        quote.current_status_type = new_quote_status_type

        db.session.add(quote)
        db.session.commit()


def _send_quote_status_email(quote, new_quote_status_type):
    if quote.current_status_type == new_quote_status_type:
        return
    
    recipients = []

    if new_quote_status_type.name == QuoteStatusType.AWAITING_APPROVAL:
        recipients = [u.email for u in get_users_for_role(ROLE_QUOTE_APPROVER)]
    elif new_quote_status_type.name == QuoteStatusType.DUE:
        recipients = [u.email for u in get_users_for_role(ROLE_QUOTE_CHARGER)]
    elif new_quote_status_type.name == QuoteStatusType.APPROVED:
        recipients = [quote.created_by]

    if recipients:
        email(
            subject=f"Quote '{quote.name}' {new_quote_status_type.name}",
            message=f"{current_user.full_name} changed quote '{quote.name}' status to '{new_quote_status_type.name}'",
            recipients=recipients,
            html_template='ui/email/quote_status_email.html',
            quote=quote,
            new_quote_status_type=new_quote_status_type,
        )


@blueprint.route("/quote/<int:quote_id>/status_history")
def quote_status_history(quote_id):
    quote = db.get_or_404(Quote, quote_id)
    statuses = QuoteStatus.query.filter(QuoteStatus.quote_id == quote.id).order_by(QuoteStatus.created_date.desc()).all()

    return render_template(
        "ui/quote/status_history.html",
        quote=quote,
        statuses=statuses,
    )
