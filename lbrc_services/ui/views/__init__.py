__all__ = [
    "task",
    "todo",
    "user",
    "reports",
    "export",
    'quote',
    'quote_requirement',
    'quote_status',
    'quote_work',
    'service',
]


import re
from datetime import timedelta, date
from sqlalchemy import or_, select
from sqlalchemy.orm import joinedload
from lbrc_services.model.quotes import Quote, QuoteStatusType
from lbrc_services.model.services import Organisation, Service, Task, TaskStatus, TaskStatusType, ToDo, User
from lbrc_flask.export import excel_download
from lbrc_flask.formatters import format_datetime


def _get_tasks_query(search_form, owner_id=None, requester_id=None):
    q = select(Task)

    if x := search_form.search.data:
        x = x.strip()
        if m := re.fullmatch(r"#(\d+)", x):
            q = q.where(Task.id == int(m.group(1)))
        else:
            for word in x.split():
                q = q.where(Task.name.like(f"%{word}%"))

    if search_form.data.get('service_id', 0) not in (0, "0", None):
        q = q.where(Task.service_id == search_form.data['service_id'])

    if search_form.data.get('organisation_id', 0) not in (0, "0", None):
        q = q.where(Task.organisations.any(Organisation.id == search_form.data['organisation_id']))

    if search_form.data.get('requestor_id', 0) not in (0, "0", None):
        q = q.where(Task.requestor_id == search_form.data['requestor_id'])

    if search_form.data.get('created_date_from', None):
        q = q.where(Task.created_date >= search_form.data['created_date_from'])

    if search_form.data.get('created_date_to', None):
        q = q.where(Task.created_date < search_form.data['created_date_to'] + timedelta(days=1))

    if 'task_status_type_id' in search_form.data:
        option = search_form.data.get('task_status_type_id', 0) or 0

        q = q.join(Task.current_status_type)

        if option == 0:
            q = q.where(TaskStatusType.is_complete == False)
        elif option == -1:
            q = q.join(Task.status_history)
            q = q.where(or_(
                TaskStatusType.is_complete == False,
                TaskStatus.created_date > (date.today() - timedelta(days=7)),
            ))
        elif option == -2:
            q = q.where(TaskStatusType.is_complete == True)
        elif option != -3:
            q = q.where(TaskStatusType.id == option)

    if owner_id is not None:
        q = q.join(Task.service)
        q = q.join(Service.owners)
        q = q.where(User.id == owner_id)

    if requester_id is not None:
        q = q.where(Task.requestor_id == requester_id)

    return q


def _get_quote_query(search_form, owner_id=None, sort_asc=False):

    q = Quote.query.options(
        joinedload(Quote.current_status_type),
    )
    if search_form.search.data:
        q = q.filter(or_(
            Quote.name.like("%{}%".format(search_form.search.data)),
            Quote.reference == search_form.search.data,
        ))

    if search_form.data.get('organisation_id', 0) not in (0, "0", None):
        q = q.filter(Quote.organisation_id == search_form.data['organisation_id'])

    if search_form.data.get('requestor_id', 0) not in (0, "0", None):
        q = q.filter(Quote.requestor_id == search_form.data['requestor_id'])

    if search_form.data.get('created_date_from', None):
        q = q.filter(Quote.created_date >= search_form.data['created_date_from'])

    if search_form.data.get('created_date_to', None):
        q = q.filter(Quote.created_date < search_form.data['created_date_to'] + timedelta(days=1))

    if 'quote_status_type_id' in search_form.data:
        option = search_form.data.get('quote_status_type_id', 0) or 0

        q = q.join(Quote.current_status_type)

        if option == 0:
            q = q.filter(QuoteStatusType.is_complete == False)
        elif option == -1:
            q = q.filter(QuoteStatusType.is_complete == True)
        elif option != -2:
            q = q.filter(QuoteStatusType.id == option)

    if sort_asc:
        q = q.order_by(Quote.created_date.asc(), Quote.id.asc())
    else:
        q = q.order_by(Quote.created_date.desc(), Quote.id.desc())

    return q


def get_todo_query(search_form):
    q = select(ToDo)

    if search_form.search.data:
        q = q.where(ToDo.name.like(f"%{search_form.search.data}%"))

    if search_form.has_value('task_id') and search_form.task_id.data:
        q = q.where(ToDo.task_id == search_form.task_id.data)

    return q


def send_task_export(title, tasks):
    # Use of dictionary instead of set to maintain order of headers
    headers = {
        'name': None,
        'organisation': None,
        'organisation description': None,
        'service': None,
        'requestor': None,
        'status': None,
        'assigned to': None,
        'created_date': None,
    }

    task_details = []

    for t in tasks:
        td = {}
        task_details.append(td)

        td['name'] = t.name
        td['organisations'] = ', '.join(o.name for o in t.organisations)
        td['organisation_description'] = t.organisation_description
        td['service'] = t.service.name
        td['requestor'] = t.requestor.full_name
        td['status'] = t.current_status_type.name
        td['created_date'] = format_datetime(t.created_date)

        if t.current_assigned_user:
            td['assigned to'] = t.current_assigned_user.full_name

        for d in t.data:
            headers[d.field.get_label()] = None

            td[d.field.get_label()] = d.formated_value
            
    return excel_download(title, headers.keys(), task_details)


def send_quote_export(title, quotes):
    # Use of dictionary instead of set to maintain order of headers
    headers = {
        'name': None,
        'organisation': None,
        'organisation description': None,
        'requestor': None,
        'status': None,
    }

    quotes_details = []

    for q in quotes:
        td = {}
        quotes_details.append(td)

        td['name'] = q.name
        td['organisation'] = q.organisation.name
        td['organisation_description'] = q.organisation_description
        td['requestor'] = q.requestor.full_name
        td['status'] = q.current_status_type.name

    return excel_download(title, headers.keys(), quotes_details)


