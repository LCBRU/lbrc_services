from flask_api import status
from flask import url_for
from lbrc_services.model import TaskStatus, TaskStatusType
from tests import get_test_task, get_test_user
from lbrc_flask.pytest.asserts import assert__requires_login


def _url(external=True, **kwargs):
    return url_for('ui.my_jobs', _external=external, **kwargs)


def _update_status_post(client, task, status, notes):
    return client.post(
        _url(),
        data={
            'task_id': task.id,
            'status': status.id,
            'notes': notes,
        },
    )


def test__post__requires_login(client):
    assert__requires_login(client, _url(external=False), post=True)


def test__my_jobs__update_status(client, faker, loggedin_user):
    s = faker.service_details(owners=[loggedin_user])

    task = get_test_task(faker, service=s)
    st = TaskStatusType.get_in_progress()
    notes = faker.pystr(min_chars=5, max_chars=10)

    resp = _update_status_post(client, task, st, notes)

    assert TaskStatus.query.filter(TaskStatus.task_id == task.id).count() == 1
    ts = TaskStatus.query.filter(TaskStatus.task_id == task.id).one()
    assert ts.task_status_type_id == st.id
    assert ts.task_id == task.id
    assert ts.notes == notes


def test__my_jobs__update_status__not_owner(client, faker, loggedin_user):
    user2 = get_test_user(faker)
    s = faker.service_details(owners=[user2])

    task = get_test_task(faker, service=s)
    st = TaskStatusType.get_in_progress()
    notes = faker.pystr(min_chars=5, max_chars=10)

    resp = _update_status_post(client, task, st, notes)
    assert resp.status_code == status.HTTP_403_FORBIDDEN
