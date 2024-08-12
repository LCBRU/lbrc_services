from datetime import datetime
import time
from flask_security import roles_required
from lbrc_flask.forms import ConfirmForm
from flask import redirect, render_template, request, url_for
from flask_login import current_user
from lbrc_services.model.quotes import Quote, QuoteRequirement, QuoteRequirementType, QuoteStatus, QuoteStatusType, QuoteWorkLine, QuoteWorkSection
from lbrc_flask.database import db
from lbrc_flask.security import get_users_for_role, User
from lbrc_flask.emailing import email
from lbrc_services.model.security import ROLE_QUOTE_CHARGER, ROLE_QUOTER, ROLE_QUOTE_APPROVER
from lbrc_services.model.services import Organisation
from lbrc_services.ui.forms import QuoteRequirementForm, QuoteSearchForm, QuoteUpdateForm, QuoteUpdateStatusForm, QuoteWorkLineForm, QuoteWorkSectionForm
from lbrc_services.ui.views import _get_quote_query, send_quote_export
from lbrc_flask.export import pdf_download
from .. import blueprint


@blueprint.route("/quotes")
@roles_required(ROLE_QUOTER)
def quotes():
    search_form = QuoteSearchForm(formdata=request.args)

    q = _get_quote_query(search_form=search_form)

    quotes = q.paginate(
            page=search_form.page.data,
            per_page=5,
            error_out=False,
        )

    return render_template(
        "ui/quote/index.html",
        quotes=quotes,
        search_form=search_form,
        quote_update_status_form=QuoteUpdateStatusForm(),
    )



@blueprint.route("/quotes/export")
def quotes_export():
    search_form = QuoteSearchForm(formdata=request.args)
    q = _get_quote_query(search_form=search_form, owner_id=current_user.id, sort_asc=True)

    return send_quote_export('My Jobs', q.all())


@blueprint.route("/quotes/update_status", methods=["POST"])
def quote_update_status():
    quote_update_status_form = QuoteUpdateStatusForm()

    if quote_update_status_form.validate_on_submit():
        status_type = db.get_or_404(QuoteStatusType, quote_update_status_form.status_type_id.data)

        _update_quote_status(
            quote_update_status_form.quote_id.data,
            status_type,
            quote_update_status_form.notes.data,
        )

    return redirect(request.args.get('prev', ''))


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


@blueprint.route("/quotes/<int:quote_id>/status_history")
def quote_status_history(quote_id):
    quote_statuses = QuoteStatus.query.filter(QuoteStatus.quote_id == quote_id).order_by(QuoteStatus.created_date.desc()).all()

    return render_template("ui/_status_history.html", quote_statuses=quote_statuses)


def save_quote(quote, form, context):

    if not quote.reference:
        requestor = db.get_or_404(User, form.requestor_id.data)
        quote.reference = f'{requestor.username}_{form.date_requested.data:%Y%m%d}_{round((time.time() % 1) * 1_000_000)}'

    quote.requestor_id = form.requestor_id.data
    quote.organisation_id = form.organisation_id.data
    quote.organisation_description = form.organisation_description.data
    quote.name = form.name.data
    quote.date_requested = form.date_requested.data
    quote.date_required = form.date_required.data
    quote.introduction = form.introduction.data
    quote.conclusion = form.conclusion.data
    quote.quote_pricing_type_id = form.quote_pricing_type_id.data

    db.session.add(quote)

    quote_status = QuoteStatus(
        quote=quote,
        quote_status_type=quote.current_status_type,
        notes='Task {} by {}'.format(context, current_user.full_name),
    )

    db.session.add(quote_status)
    db.session.commit()


@blueprint.route("/quotes/create", methods=["GET", "POST"])
@roles_required(ROLE_QUOTER)
def create_quote():
    form = QuoteUpdateForm()

    if form.validate_on_submit():
        quote = Quote(
            current_status_type=QuoteStatusType.get_draft(),
        )

        save_quote(quote, form, 'created')

        return redirect(url_for("ui.quotes"))

    return render_template(
        "ui/quote/create.html",
        form=form,
        other_organisation=Organisation.get_other(),
    )


@blueprint.route("/quotes/<int:quote_id>/edit", methods=["GET", "POST"])
@roles_required(ROLE_QUOTER)
def edit_quote(quote_id):
    quote = db.get_or_404(Quote, quote_id)

    form = QuoteUpdateForm(obj=quote)

    if form.validate_on_submit():

        save_quote(quote, form, 'updated')

        return redirect(request.args.get('prev', ''))

    return render_template(
        "ui/quote/create.html",
        form=form,
        other_organisation=Organisation.get_other(),
    )


@blueprint.route("/quotes/<int:quote_id>/requirements")
@roles_required(ROLE_QUOTER)
def edit_quote_requirements(quote_id):
    return render_template(
        "ui/quote/requirements.html",
        quote=db.get_or_404(Quote, quote_id),
        types=QuoteRequirementType.query.order_by(QuoteRequirementType.importance.desc()).order_by(QuoteRequirementType.name).all(),
        quote_edit_form=QuoteRequirementForm(),
        delete_form=ConfirmForm(),
    )


@blueprint.route("/quotes/requirements/save", methods=["POST"])
@roles_required(ROLE_QUOTER)
def save_quote_requirement():
    form = QuoteRequirementForm()

    if form.validate_on_submit():
        quote = db.get_or_404(Quote, form.quote_id.data)
        requirement_type = db.get_or_404(QuoteRequirementType, form.quote_requirement_type_id.data)

        requirement = QuoteRequirement.query.filter(QuoteRequirement.id == form.id.data).one_or_none()

        if not requirement:
            requirement = QuoteRequirement(
                quote=quote,
            )

        requirement.quote_requirement_type = requirement_type
        requirement.notes = form.notes.data

        db.session.add(requirement)
        db.session.commit()

    return redirect(request.args.get('prev', url_for('ui.quotes')))


@blueprint.route("/quotes/requirements/delete", methods=['POST'])
def delete_quote_requirement():
    form = ConfirmForm()

    if form.validate_on_submit():
        r = db.get_or_404(QuoteRequirement, form.id.data)
        db.session.delete(r)
        db.session.commit()

    return redirect(request.args.get('prev', url_for('ui.quotes')))


@blueprint.route("/quotes/<int:quote_id>/work")
@roles_required(ROLE_QUOTER)
def edit_quote_work(quote_id):
    return render_template(
        "ui/quote/work.html",
        quote=db.get_or_404(Quote, quote_id),
        quote_work_section_form=QuoteWorkSectionForm(),
        quote_work_line_form=QuoteWorkLineForm(),
        delete_form=ConfirmForm(),
    )


@blueprint.route("/quotes/work/sections/save", methods=["POST"])
@roles_required(ROLE_QUOTER)
def save_quote_work_section():
    form = QuoteWorkSectionForm()

    if form.validate_on_submit():
        quote = db.get_or_404(Quote, form.quote_id.data)
        section = QuoteWorkSection.query.filter(QuoteWorkSection.id == form.id.data).one_or_none()

        if not section:
            section = QuoteWorkSection(
                quote=quote,
            )

        section.name = form.name.data

        db.session.add(section)
        db.session.commit()

    return redirect(request.args.get('prev', url_for('ui.quotes')))


@blueprint.route("/quotes/work/sections/delete", methods=['POST'])
def delete_quote_work_section():
    form = ConfirmForm()

    if form.validate_on_submit():
        s = db.get_or_404(QuoteWorkSection, form.id.data)

        for l in s.lines:
            db.session.delete(l)
        db.session.delete(s)
        db.session.commit()

    return redirect(request.args.get('prev', url_for('ui.quotes')))


@blueprint.route("/quotes/work/line/save", methods=["POST"])
@roles_required(ROLE_QUOTER)
def save_quote_work_line():
    form = QuoteWorkLineForm()

    if form.validate_on_submit():
        qws = db.get_or_404(QuoteWorkSection, form.quote_work_section_id.data)
        line = QuoteWorkLine.query.filter(QuoteWorkLine.id == form.id.data).one_or_none()

        if not line:
            line = QuoteWorkLine(
                quote_work_section=qws,
            )

        line.name = form.name.data
        line.days = form.days.data

        db.session.add(line)
        db.session.commit()

    return redirect(request.args.get('prev', url_for('ui.quotes')))


@blueprint.route("/quotes/work/line/delete", methods=['POST'])
def delete_quote_work_line():
    form = ConfirmForm()

    if form.validate_on_submit():
        l = db.get_or_404(QuoteWorkLine, form.id.data)

        print(l)

        db.session.delete(l)
        db.session.commit()

    return redirect(request.args.get('prev', url_for('ui.quotes')))


@blueprint.route("/quotes/<int:quote_id>/pdf")
def quote_pdf(quote_id):
    quote = db.get_or_404(Quote, quote_id)

    return pdf_download('ui/quote/pdf.html', title=f'quote_{quote.reference}', quote=quote, path='./lbrc_services/ui/templates/ui/quote/')
