from itertools import groupby
import pygal
from pygal.style import Style
from collections import Counter
from dateutil.rrule import rrule, MONTHLY
from datetime import date
from flask import render_template, current_app
from flask_security import current_user
from lbrc_services.model import Task, Service, TaskStatusType
from sqlalchemy.sql import func
from ..decorators import must_own_a_service
from .. import blueprint
from lbrc_flask.database import db

@blueprint.route("/reports")
@must_own_a_service()
def reports():
    return render_template("ui/reports.html")


def sqlalchemy_format_date():
    current_app.logger.error(db.session.bind.dialect.name)
    return None

@blueprint.route("/reports/service_tasks_requested_by_month")
@must_own_a_service()
def service_tasks_requested_by_month():

    date_formatter = sqlalchemy_format_date()

    tasks = Task.query.with_entities(
        Service.name,
        Task.created_date,
        # func.strftime('%b %Y',Task.created_date),
    ).join(
        Task.service,
    ).filter(
        Task.service_id.in_([u.id for u in current_user.owned_services])
    ).order_by(
        Service.name,
        Task.created_date,
    ).all()

    min_date = min([t[1] for t in tasks])
    max_date = max([t[1] for t in tasks])

    buckets = [d.strftime('%b %Y') for d in rrule(
        MONTHLY,
        dtstart=date(min_date.year, min_date.month, 1),
        until=date(max_date.year, max_date.month, 1),
    )]

    chart = pygal.Bar(style=Style(font_family='Lato'))
    chart.title = 'Service Tasks Requested by Month'
    chart.x_labels = buckets

    for service_name, service_tasks in groupby(tasks, lambda t: t[0]):
        count = Counter([t[1].strftime('%b %Y') for t in service_tasks])
        month_range_count = {b: count.get(b, 0) for b in buckets}

        chart.add(service_name, month_range_count.values())

    return chart.render_response()


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

    chart = pygal.Bar(style=Style(font_family='Lato'))
    chart.title = 'Service Tasks by Current Status'
    chart.x_labels = buckets

    for service_name, service_tasks in groupby(tasks, lambda t: t[0]):
        count = Counter([t[1] for t in service_tasks])
        values = {b: count.get(b, 0) for b in buckets}

        chart.add(service_name, values.values())

    return chart.render_response()
