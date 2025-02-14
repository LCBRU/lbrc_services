from flask_security import roles_required
from lbrc_flask.forms import ConfirmForm
from flask import redirect, render_template, request, url_for
from lbrc_services.model.quotes import Quote, QuoteWorkLine, QuoteWorkSection
from lbrc_flask.database import db
from lbrc_services.model.security import ROLE_QUOTER
from .. import blueprint
from flask import url_for
from lbrc_flask.forms import FlashingForm, DataListField
from wtforms import StringField
from wtforms.fields import DecimalField
from wtforms.fields.simple import HiddenField
from wtforms.validators import DataRequired, NumberRange
from lbrc_services.model.quotes import QuoteWorkLineNameSuggestion
from lbrc_flask.response import refresh_details, REFRESH_DETAILS_TRIGGER


class QuoteWorkSectionForm(FlashingForm):
    name = StringField('Name', validators=[DataRequired()])


class QuoteWorkLineForm(FlashingForm):
    name = StringField('Name', validators=[DataRequired()], render_kw={'list': 'name_options', 'autocomplete': 'off' })
    name_options = DataListField()
    days = DecimalField('Days', places=2, render_kw={'min': '0', 'max': '50', 'step': '0.25'}, validators=[DataRequired(), NumberRange(min=0, max=50)])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.name_options.choices = [s.name for s in QuoteWorkLineNameSuggestion.query.all()]


@blueprint.route("/quote/<int:quote_id>/work_section/add", methods=["GET", "POST"])
@roles_required(ROLE_QUOTER)
def quote_work_section_add(quote_id):
    quote = db.get_or_404(Quote, quote_id)

    form = QuoteWorkSectionForm()

    if form.validate_on_submit():
        obj = QuoteWorkSection(
            quote=quote,
            name=form.name.data,
        )
        db.session.add(obj)
        db.session.commit()
        return refresh_details()

    return render_template(
        "lbrc/form_modal.html",
        title=f"Add Work Section to quote {quote.name}",
        form=form,
        url=url_for('ui.quote_work_section_add', quote_id=quote.id),
        closing_events=[REFRESH_DETAILS_TRIGGER],
    )


@blueprint.route("/quote/<int:quote_id>/work_section/<int:quote_work_section_id>/edit", methods=["GET", "POST"])
@roles_required(ROLE_QUOTER)
def quote_work_section_edit(quote_id, quote_work_section_id):
    quote = db.get_or_404(Quote, quote_id)
    quote_work_section = db.get_or_404(QuoteWorkSection, quote_work_section_id)

    form = QuoteWorkSectionForm(obj=quote_work_section)

    if form.validate_on_submit():
        quote_work_section.name = form.name.data
        db.session.add(quote_work_section)
        db.session.commit()
        return refresh_details()

    return render_template(
        "lbrc/form_modal.html",
        title=f"Edit Work Section on quote {quote.name}",
        form=form,
        url=url_for('ui.quote_work_section_edit', quote_id=quote.id, quote_work_section_id=quote_work_section.id),
        closing_events=[REFRESH_DETAILS_TRIGGER],
    )


@blueprint.route("/quote/<int:quote_id>/work_section/<int:quote_work_section_id>/delete", methods=['POST'])
def quote_work_section_delete(quote_id, quote_work_section_id):
    quote = db.get_or_404(Quote, quote_id)
    s = db.get_or_404(QuoteWorkSection, quote_work_section_id)

    for l in s.lines:
        db.session.delete(l)
    db.session.delete(s)
    db.session.commit()

    return refresh_details()


@blueprint.route("/quote/<int:quote_id>/work_section/<int:quote_work_section_id>/work_line/add", methods=["GET", "POST"])
@roles_required(ROLE_QUOTER)
def quote_work_line_add(quote_id, quote_work_section_id):
    quote = db.get_or_404(Quote, quote_id)
    quote_work_section = db.get_or_404(QuoteWorkSection, quote_work_section_id)

    form = QuoteWorkLineForm()

    if form.validate_on_submit():
        obj = QuoteWorkLine(
            quote_work_section=quote_work_section,
            name=form.name.data,
            days=form.days.data,
        )
        db.session.add(obj)
        db.session.commit()
        return refresh_details()

    return render_template(
        "lbrc/form_modal.html",
        title=f"Add Line to Work Section {quote_work_section.name}",
        form=form,
        url=url_for('ui.quote_work_line_add', quote_id=quote.id, quote_work_section_id=quote_work_section.id),
        closing_events=[REFRESH_DETAILS_TRIGGER],
    )


@blueprint.route("/quote/<int:quote_id>/work_section/<int:quote_work_section_id>/work_line/<int:quote_work_line_id>/edit", methods=["GET", "POST"])
@roles_required(ROLE_QUOTER)
def quote_work_line_edit(quote_id, quote_work_section_id, quote_work_line_id):
    quote = db.get_or_404(Quote, quote_id)
    quote_work_section = db.get_or_404(QuoteWorkSection, quote_work_section_id)
    quote_work_line = db.get_or_404(QuoteWorkLine, quote_work_line_id)

    form = QuoteWorkLineForm(obj=quote_work_line)

    if form.validate_on_submit():
        quote_work_line.name = form.name.data
        quote_work_line.days = form.days.data
        db.session.add(quote_work_line)
        db.session.commit()
        return refresh_details()

    return render_template(
        "lbrc/form_modal.html",
        title=f"Edit Work Line for Section {quote_work_section.name}",
        form=form,
        url=url_for('ui.quote_work_section_edit', quote_id=quote.id, quote_work_section_id=quote_work_section.id, quote_work_line_id=quote_work_line.id),
        closing_events=[REFRESH_DETAILS_TRIGGER],
    )


@blueprint.route("/quote/<int:quote_id>/work_section/<int:quote_work_section_id>/work_line/<int:quote_work_line_id>/delete", methods=['POST'])
def quote_work_line_delete(quote_id, quote_work_section_id, quote_work_line_id):
    quote = db.get_or_404(Quote, quote_id)
    quote_work_section = db.get_or_404(QuoteWorkSection, quote_work_section_id)
    quote_work_line = db.get_or_404(QuoteWorkLine, quote_work_line_id)

    db.session.delete(quote_work_line)
    db.session.commit()

    return refresh_details()
