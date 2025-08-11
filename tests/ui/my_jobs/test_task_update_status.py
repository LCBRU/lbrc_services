import http
from flask import url_for
from lbrc_services.model.services import TaskStatus, TaskStatusType
from lbrc_flask.pytest.asserts import assert__requires_login


def _url(external=True, **kwargs):
    return url_for('ui.task_update_status', _external=external, **kwargs)


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
    task = faker.get_test_owned_task(owner=loggedin_user)

    st = TaskStatusType.get_in_progress()
    notes = faker.pystr(min_chars=5, max_chars=10)

    resp = _update_status_post(client, task, st, notes)

    assert TaskStatus.query.filter(TaskStatus.task_id == task.id).count() == 1
    ts = TaskStatus.query.filter(TaskStatus.task_id == task.id).one()
    assert ts.task_status_type_id == st.id
    assert ts.task_id == task.id
    assert ts.notes == notes


def test__my_jobs__update_status__not_owner(client, faker, loggedin_user):
    user2 = faker.get_test_user()

    task = faker.get_test_owned_task(owner=user2)

    st = TaskStatusType.get_in_progress()
    notes = faker.pystr(min_chars=5, max_chars=10)

    resp = _update_status_post(client, task, st, notes)
    assert resp.status_code == http.HTTPStatus.FORBIDDEN
