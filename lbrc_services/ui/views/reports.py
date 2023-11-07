from lbrc_flask.forms.dynamic import Field
from lbrc_services.ui.views import _get_tasks_query
from dateutil.rrule import rrule, MONTHLY
from datetime import date, datetime
from flask import render_template, request, send_file
from flask_security import current_user
from ..decorators import must_be_service_owner, must_own_a_service
from .. import blueprint
from lbrc_flask.charting import grouped_bar_chart
from ..forms import ReportSearchForm
from tempfile import NamedTemporaryFile


@blueprint.route("/reports")
@must_own_a_service()
@must_be_service_owner('service_id')
def reports():
    search_form = ReportSearchForm(formdata=request.args)

    return render_template("ui/reports.html", search_form=search_form, chart=get_chart(search_form).render_data_uri())


@blueprint.route("/report_png")
@must_own_a_service()
@must_be_service_owner('service_id')
def report_png():
    search_form = ReportSearchForm(formdata=request.args)

    chart = get_chart(search_form)
    report_grouper_id = search_form.data.get('report_grouper_id', -3)

    with NamedTemporaryFile() as tmp:
        chart.render_to_png(tmp.name)

        return send_file(
            tmp.name,
            as_attachment=True,
            download_name='{}_{}.png'.format(get_report_name(report_grouper_id), datetime.utcnow().strftime("%Y%m%d_%H%M%S")),
            cache_timeout=0,
            mimetype='image/png',
        )


def get_chart(search_form):
    tasks = _get_tasks_query(search_form=search_form, requester_id=current_user.id).all()

    report_grouper_id = search_form.data.get('report_grouper_id', -3)
    buckets = None

    if report_grouper_id == -3:
        if len(tasks) < 1:
            buckets = []
        else:
            min_date = min([t.created_date for t in tasks])
            max_date = max([t.created_date for t in tasks])

            buckets = [d.strftime('%b %Y') for d in rrule(
                MONTHLY,
                dtstart=date(min_date.year, min_date.month, 1),
                until=date(max_date.year, max_date.month, 1),
            )]

        group_category = [{'group': t.service.name, 'category': t.created_date.strftime('%b %Y')} for t in tasks]

    elif report_grouper_id == -2:
        group_category = [{'group': t.service.name, 'category': t.current_status_type.name} for t in tasks]

    elif report_grouper_id == -1:
        group_category = [{'group': t.service.name, 'category': t.organisation.name} for t in tasks]
    
    else:
        field = db.get_or_404(Field, report_grouper_id)

        if len(field.get_choices()) > 0:
            buckets = [c[0] for c in field.get_choices() if c[0]]
        
        group_category = []

        for t in tasks:
            group_category.extend([{'group': t.service.name, 'category': d.formated_value} for d in t.data if d.field_id == report_grouper_id])

    return grouped_bar_chart(get_report_name(report_grouper_id), group_category, buckets=buckets)


def get_report_name(report_id):
    static_groupers = {
        -3: 'Month Requested',
        -2: 'Current Status',
        -1: 'Organisation',
    }

    if report_id in static_groupers.keys():
        grouper = static_groupers[report_id]
    else:
        grouper = db.get_or_404(Field, report_id).get_label()

    return 'Jobs by {}'.format(grouper)

