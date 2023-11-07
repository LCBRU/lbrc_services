from lbrc_flask.forms.dynamic import Field
from lbrc_services.ui.views import _get_tasks_query
from flask import render_template, request
from flask_security import current_user
from ..decorators import must_be_service_owner, must_own_a_service
from .. import blueprint
from ..forms import ReportSearchForm
from lbrc_flask.database import db
from lbrc_flask.charting import BarChart, BarChartItem


@blueprint.route("/reports")
@must_own_a_service()
@must_be_service_owner('service_id')
def reports():
    search_form = ReportSearchForm(formdata=request.args)

    return render_template("ui/reports.html", search_form=search_form, chart=get_chart(search_form).get_chart().render_data_uri())


@blueprint.route("/report_png")
@must_own_a_service()
@must_be_service_owner('service_id')
def report_png():
    search_form = ReportSearchForm(formdata=request.args)

    chart = get_chart(search_form)
    chart.send_as_attachment()


def get_chart(search_form):
    tasks = list(db.session.execute(_get_tasks_query(search_form=search_form)).unique().scalars())

    report_grouper_id = search_form.data.get('report_grouper_id', -3)

    if report_grouper_id == -3:
        group_category = [BarChartItem(
            series=t.service.name,
            bucket=t.created_date.strftime('%b %Y'),
        ) for t in tasks]

    elif report_grouper_id == -2:
        group_category = [BarChartItem(
            series=t.service.name,
            bucket=t.current_status_type.name,
        ) for t in tasks]

    elif report_grouper_id == -1:
        group_category = []
        for t in tasks:
            for o in t.organisations:
                group_category.append(BarChartItem(
                    series=t.service.name,
                    bucket=o.name,
                ))
    else:
        group_category = []

        for t in tasks:
            group_category.extend([
                BarChartItem(
                    series=t.service.name,
                    bucket=d.formated_value,
                ) for d in t.data if d.field_id == report_grouper_id
            ])

    bc: BarChart = BarChart(
        title=get_report_name(report_grouper_id),
        items=group_category,
        y_title='Jobs',
    )

    return bc


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

