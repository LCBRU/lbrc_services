from flask_security import roles_required
from flask import render_template, url_for
from lbrc_services.model.quotes import Quote, QuoteRequirement, QuoteRequirementType
from lbrc_flask.database import db
from lbrc_services.model.security import ROLE_QUOTER
from lbrc_flask.response import refresh_details, REFRESH_DETAILS_TRIGGER
from .. import blueprint
from flask import url_for
from lbrc_flask.forms import FlashingForm
from lbrc_flask.database import db
from wtforms import TextAreaField
from wtforms.fields.simple import HiddenField
from lbrc_services.model.quotes import QuoteRequirementType


class QuoteRequirementForm(FlashingForm):
    id = HiddenField()
    notes = TextAreaField('Notes')


@blueprint.route("/quote/<int:quote_id>/requirement_type/<int:quote_requirement_type_id>/add", methods=["GET", "POST"])
@roles_required(ROLE_QUOTER)
def add_quote_requirement(quote_id, quote_requirement_type_id):
    quote = db.get_or_404(Quote, quote_id)
    quote_requirement_type = db.get_or_404(QuoteRequirementType, quote_requirement_type_id)

    form = QuoteRequirementForm()

    if form.validate_on_submit():
        quote_requirement = QuoteRequirement(
            quote=quote,
            quote_requirement_type=quote_requirement_type,
            notes=form.notes.data,
        )
        db.session.add(quote_requirement)
        db.session.commit()
        return refresh_details()

    return render_template(
        "lbrc/form_modal.html",
        title=f"Add {quote_requirement_type.name} Requirement for Quote",
        form=form,
        url=url_for('ui.add_quote_requirement', quote_id=quote.id, quote_requirement_type_id=quote_requirement_type.id),
        closing_events=[REFRESH_DETAILS_TRIGGER],
    )


@blueprint.route("/quote/<int:quote_id>/requirement/<int:quote_requirement_id>/edit", methods=["GET", "POST"])
@roles_required(ROLE_QUOTER)
def edit_quote_requirement(quote_id, quote_requirement_id):
    quote = db.get_or_404(Quote, quote_id)
    quote_requirement = db.get_or_404(QuoteRequirement, quote_requirement_id)

    form = QuoteRequirementForm(obj=quote_requirement)

    if form.validate_on_submit():
        quote_requirement.notes=form.notes.data
        db.session.add(quote_requirement)
        db.session.commit()
        return refresh_details()

    return render_template(
        "lbrc/form_modal.html",
        title=f"Edit {quote_requirement.quote_requirement_type.name} Requirement for Quote",
        form=form,
        url=url_for('ui.edit_quote_requirement', quote_id=quote.id, quote_requirement_id=quote_requirement.id),
        closing_events=[REFRESH_DETAILS_TRIGGER],
    )


@blueprint.route("/quote/<int:quote_id>/requirement/<int:quote_requirement_id>/delete", methods=['POST'])
@roles_required(ROLE_QUOTER)
def delete_quote_requirement(quote_id, quote_requirement_id):
    quote = db.get_or_404(Quote, quote_id)
    r = db.get_or_404(QuoteRequirement, quote_requirement_id)
    db.session.delete(r)
    db.session.commit()

    return refresh_details()
