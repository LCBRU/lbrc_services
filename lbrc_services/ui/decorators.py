from functools import wraps
from flask import abort
from flask_login import current_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from lbrc_flask.requests import get_value_from_all_arguments
from lbrc_requests.model import RequestFile, Request, RequestType, User


def must_be_request_file_owner_or_requestor(var_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rf = RequestFile.query.options(
                joinedload(RequestFile.request).joinedload(Request.request_type).joinedload(RequestType.owners),
            ).get_or_404(get_value_from_all_arguments(var_name))

            if rf.request.requestor_id != current_user.id and current_user not in rf.request.request_type.owners:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def must_be_request_owner_or_requestor(var_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            r = Request.query.options(
                joinedload(Request.request_type).joinedload(RequestType.owners),
            ).get_or_404(get_value_from_all_arguments(var_name))

            if r.requestor_id != current_user.id and current_user not in r.request_type.owners:
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator
