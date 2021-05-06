from dateutil.rrule import rrule, MONTHLY
from datetime import date
from flask import render_template
from flask_security import current_user
from lbrc_services.model import Task, Service, TaskStatusType
from lbrc_flask.database import dialect_date_format_string, dialect_format_date
from ..decorators import must_own_a_service
from .. import blueprint
from lbrc_flask.validators import parse_date
from lbrc_flask.charting import grouped_bar_chart


@blueprint.route("/reports")
@must_own_a_service()
def reports():
    return render_template("ui/reports.html")


@blueprint.route("/reports/service_tasks_requested_by_month")
@must_own_a_service()
def service_tasks_requested_by_month():
    date_format_string = dialect_date_format_string('%b %Y')

    tasks = Task.query.with_entities(
        Service.name,
        dialect_format_date(Task.created_date, date_format_string),
    ).join(
        Task.service,
    ).filter(
        Task.service_id.in_([u.id for u in current_user.owned_services])
    ).order_by(
        Service.name,
        Task.created_date,
    ).all()

    min_date = min([parse_date(t[1]) for t in tasks])
    max_date = max([parse_date(t[1]) for t in tasks])

    buckets = [d.strftime(date_format_string) for d in rrule(
        MONTHLY,
        dtstart=date(min_date.year, min_date.month, 1),
        until=date(max_date.year, max_date.month, 1),
    )]

    return grouped_bar_chart('Service Tasks Requested by Month', buckets, tasks)


@blueprint.route("/reports/service_tasks_by_current_status")
@must_own_a_service()
def service_tasks_by_current_status():

    tasks = Task.query.with_entities(
        Service.name,
        TaskStatusType.name,
    ).join(
        Task.service,
        Task.current_status_type,
    ).filter(
        Task.service_id.in_([u.id for u in current_user.owned_services])
    ).order_by(
        Service.name,
        Task.created_date,
    ).all()

    buckets = {t[1] for t in tasks}

    return grouped_bar_chart('Service Tasks by Current Status', buckets, tasks)
