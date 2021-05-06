from itertools import groupby
import pygal
from pygal.style import Style
from collections import Counter
from dateutil.rrule import rrule, MONTHLY
from datetime import date
from flask import render_template
from flask_security import current_user
from lbrc_services.model import Task, Service
from ..decorators import must_own_a_service
from .. import blueprint

@blueprint.route("/reports")
@must_own_a_service()
def reports():
    return render_template("ui/reports.html")


@blueprint.route("/reports/by_date")
@must_own_a_service()
def report_by_date():

    tasks = Task.query.with_entities(
        Service.name,
        Task.created_date,
    ).join(
        Task.service
    ).filter(
        Task.service_id.in_([u.id for u in current_user.owned_services])
    ).order_by(
        Service.name,
        Task.created_date,
    ).all()

    min_date = min([t[1] for t in tasks])
    max_date = max([t[1] for t in tasks])

    buckets = list(rrule(
        MONTHLY,
        dtstart=date(min_date.year, min_date.month, 1),
        until=date(max_date.year, max_date.month, 1),
    ))

    chart = pygal.Bar(style=Style(font_family='Lato'))
    chart.title = 'Service Tasks by Requested Month'
    chart.x_labels = [b.strftime('%b %Y') for b in buckets]

    for service_name, service_tasks in groupby(tasks, lambda t: t[0]):
        count = Counter([(t[1].year, t[1].month) for t in service_tasks])
        month_range_count = {
            d.strftime('%b %Y'): count.get((d.year, d.month), 0)
            for d in buckets}

        chart.add(service_name, month_range_count.values())

    return chart.render_response()
