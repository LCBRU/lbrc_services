from tests import get_test_service, get_test_task, get_test_todo
from lbrc_services.model import ToDo


def get_test_owned_todo(faker, user, status_name=None):
    if status_name is None:
        status_name = ToDo.OUTSTANDING

    s = get_test_service(faker, owners=[user])
    task = get_test_task(faker, service=s)
    todo = get_test_todo(faker, task=task, status=ToDo.get_status_code_from_name(status_name))
    return todo
