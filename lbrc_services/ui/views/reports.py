from flask import render_template, request

from lbrc_services.ui.view_models.reports import CurrentStatusReport, FieldReport, MonthRequestedReport, OrganisationReport
from ..decorators import must_be_service_owner, must_own_a_service
from .. import blueprint
from ..forms import ReportSearchForm


@blueprint.route("/reports")
@must_own_a_service()
@must_be_service_owner('service_id')
def reports():
    search_form = ReportSearchForm(formdata=request.args)

    return render_template(
        "ui/reports.html",
        search_form=search_form,
    )


@blueprint.route("/reports/image")
@blueprint.route("/reports/image/<string:type>")
def report_image(type='png'):
    search_form = ReportSearchForm(search_placeholder='Search Requests', formdata=request.args)

    chart = get_report(search_form)

    bc = chart.get_chart()

    if type == 'svg':
        return bc.send_svg()
    elif type == 'attachment':
        return bc.send_as_attachment()
    elif type == 'table':
        return bc.send_table()
    else:
        return bc.send()

@blueprint.route("/report/image_panel", methods=['GET', 'POST'])
def image_panel():
    search_form = ReportSearchForm(formdata=request.args)

    return render_template(
        "ui/reports/image.html",
        search_form=search_form,
    )

@blueprint.route("/report/table_panel", methods=['GET', 'POST'])
def table_panel():
    search_form = ReportSearchForm(formdata=request.args)

    return render_template(
        "ui/reports/table.html",
        title=get_report(search_form).get_report_name(),
        search_form=search_form,
    )

def get_report(search_form):
    report_grouper_id = search_form.data.get('report_grouper_id', -3)

    if report_grouper_id == -3:
        return MonthRequestedReport(search_form)
    elif report_grouper_id == -2:
        return CurrentStatusReport(search_form)
    elif report_grouper_id == -1:
        return OrganisationReport(search_form)
    else:
        return FieldReport(search_form, report_grouper_id)
