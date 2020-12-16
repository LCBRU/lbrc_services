from functools import wraps
from flask import abort
from flask_login import current_user
from sqlalchemy import or_
from lbrc_flask.requests import get_value_from_all_arguments
from lbrc_requests.model import RequestFile, Request, RequestType, User


def must_be_request_file_owner_or_requestor(var_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if (RequestFile.query.\
                filter(RequestFile.id == get_value_from_all_arguments(var_name)).\
                join(RequestFile.request).\
                join(Request.request_type).\
                join(RequestType.owners).\
                filter(or_(
                    User.id == current_user.id,
                    Request.requestor_id == current_user.id,
                )).count() == 0
            ):
                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


