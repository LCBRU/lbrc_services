import time
from flask_security import roles_required
from flask import render_template, render_template_string, request, url_for
from flask_login import current_user
from sqlalchemy import select
from lbrc_services.model.quotes import Quote, QuoteRequirementType, QuoteStatus, QuoteStatusType
from lbrc_flask.database import db
from lbrc_flask.security import User
from lbrc_services.model.security import ROLE_QUOTER
from lbrc_services.model.services import Organisation
from lbrc_services.ui.forms import QuoteSearchForm, QuoteUpdateForm
from lbrc_services.ui.views import _get_quote_query, send_quote_export
from lbrc_flask.export import pdf_download
from lbrc_flask.response import refresh_response
from .. import blueprint


## Quotes

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
    )



@blueprint.route("/quote/<int:id>/<string:detail_selector>")
def quote_details(id, detail_selector):
    quote = db.get_or_404(Quote, id)
    requirement_types = db.session.execute(
        select(QuoteRequirementType)
        .order_by(QuoteRequirementType.importance.desc())
        .order_by(QuoteRequirementType.name)
    ).scalars()

    template = '''
        {% from "ui/quote/_details.html" import render_quote_details with context %}
        {{ render_quote_details(quote, detail_selector) }}
    '''

    return render_template_string(
        template,
        quote=quote,
        detail_selector=detail_selector,
        requirement_types=requirement_types,
    )


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

        return refresh_response()

    return render_template(
        "ui/quote/create.html",
        form=form,
        title="Add Quote",
        other_organisation=Organisation.get_other(),
        url=url_for('ui.create_quote'),
    )


@blueprint.route("/quotes/<int:quote_id>/edit", methods=["GET", "POST"])
@roles_required(ROLE_QUOTER)
def edit_quote(quote_id):
    quote = db.get_or_404(Quote, quote_id)

    form = QuoteUpdateForm(obj=quote)

    if form.validate_on_submit():

        save_quote(quote, form, 'updated')

        return refresh_response()

    return render_template(
        "ui/quote/create.html",
        form=form,
        title="Edit Quote",
        other_organisation=Organisation.get_other(),
        url=url_for('ui.edit_quote', quote_id=quote.id),
    )


# Quote Exports and PDFs

@blueprint.route("/quotes/export")
def quotes_export():
    search_form = QuoteSearchForm(formdata=request.args)
    q = _get_quote_query(search_form=search_form, owner_id=current_user.id, sort_asc=True)

    return send_quote_export('My Jobs', q.all())


@blueprint.route("/quotes/<int:quote_id>/pdf")
def quote_pdf(quote_id):
    quote = db.get_or_404(Quote, quote_id)

    return pdf_download('ui/quote/pdf.html', title=f'quote_{quote.reference}', quote=quote, path='./lbrc_services/ui/templates/ui/quote/')
