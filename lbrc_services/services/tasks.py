
import re
from datetime import date, timedelta
from sqlalchemy import or_, select
from lbrc_services.model.services import Organisation, Service, Task, TaskStatus, TaskStatusType, User


def task_search_query(search_data: dict, **kwargs):
    search_data.update(kwargs)

    q = select(Task)

    if x := search_data.get('search'):
        x = x.strip()
        if m := re.fullmatch(r"#(\d+)", x):
            q = q.where(Task.id == int(m.group(1)))
        else:
            for word in x.split():
                q = q.where(Task.name.like(f"%{word}%"))

    if (x := search_data.get('service_id', 0)) not in (0, "0", None):
        q = q.where(Task.service_id == x)

    if (x := search_data.get('organisation_id', 0)) not in (0, "0", None):
        q = q.where(Task.organisations.any(Organisation.id == x))

    if (x := search_data.get('requestor_id', 0)) not in (0, "0", None):
        q = q.where(Task.requestor_id == x)

    if (x := search_data.get('created_date_from', None)):
        q = q.where(Task.created_date >= x)

    if (x := search_data.get('created_date_to', None)):
        q = q.where(Task.created_date < x + timedelta(days=1))

    task_status_type_id = search_data.get('task_status_type_id', 0) or 0

    q = q.join(Task.current_status_type)

    if task_status_type_id == 0:
        q = q.where(TaskStatusType.is_complete == False)
    elif task_status_type_id == -1:
        q = q.join(Task.status_history)
        q = q.where(or_(
            TaskStatusType.is_complete == False,
            TaskStatus.created_date > (date.today() - timedelta(days=7)),
        ))
    elif task_status_type_id == -2:
        q = q.where(TaskStatusType.is_complete == True)
    elif task_status_type_id != -3:
        q = q.where(TaskStatusType.id == task_status_type_id)

    if (x := kwargs.get('owner_id')):
        q = q.join(Task.service)
        q = q.join(Service.owners)
        q = q.where(User.id == x)

    if (x := kwargs.get('requester_id')):
        q = q.where(Task.requestor_id == x)

    return q
