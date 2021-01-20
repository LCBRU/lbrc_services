from functools import wraps
from flask import abort
from flask_login import current_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from lbrc_flask.requests import get_value_from_all_arguments
from lbrc_services.model import TaskFile, Task, Service, ToDo


def must_be_task_file_owner_or_requestor(var_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rf = TaskFile.query.options(
                joinedload(TaskFile.task).joinedload(Task.service).joinedload(Service.owners),
            ).get_or_404(get_value_from_all_arguments(var_name))

            if rf.task.requestor_id != current_user.id and current_user not in rf.task.service.owners:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def must_be_task_owner_or_requestor(var_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            r = Task.query.options(
                joinedload(Task.service).joinedload(Service.owners),
            ).get_or_404(get_value_from_all_arguments(var_name))

            if r.requestor_id != current_user.id and current_user not in r.service.owners:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def must_be_todo_owner(var_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            print('A' * 100)
            print(var_name)
            print(get_value_from_all_arguments(var_name))
            r = ToDo.query.options(
                joinedload(ToDo.task).joinedload(Task.service).joinedload(Service.owners),
            ).get_or_404(get_value_from_all_arguments(var_name))
            print('B' * 100)

            if current_user not in r.task.service.owners:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator
