from functools import wraps
from flask import abort
from flask_login import current_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from lbrc_flask.requests import get_value_from_all_arguments
from lbrc_flask.database import db
from lbrc_services.model.services import TaskFile, Task, Service, ToDo


def must_own_a_service():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.service_owner:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def must_be_service_owner(var_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            service_id = get_value_from_all_arguments(var_name)

            if service_id is not None and int(service_id) > 0:
                s = db.get_or_404(Service, service_id)

                if current_user not in s.owners:
                    abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def must_be_task_file_owner_or_requestor(var_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            x = get_value_from_all_arguments(var_name)
            rf = db.get_or_404(TaskFile, get_value_from_all_arguments(var_name))

            if rf.task.requestor_id != current_user.id and current_user not in rf.task.service.owners:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def must_be_task_owner(var_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            r = db.get_or_404(Task, get_value_from_all_arguments(var_name))

            if current_user not in r.service.owners:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def must_be_task_owner_or_requestor(var_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            r = db.get_or_404(Task, get_value_from_all_arguments(var_name))

            if r.requestor_id != current_user.id and current_user not in r.service.owners:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def must_be_todo_owner(var_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            r = db.get_or_404(ToDo, get_value_from_all_arguments(var_name))

            if current_user not in r.task.service.owners:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator
