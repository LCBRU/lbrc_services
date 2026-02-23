import http
from flask import url_for
from lbrc_services.model.services import TaskStatus, TaskStatusType
from lbrc_flask.pytest.asserts import assert__requires_login
from sqlalchemy import select
from lbrc_flask.database import db


def _url(external=True, **kwargs):
    return url_for('ui.task_update_status', _external=external, **kwargs)


def _update_status_post(client, task, status, notes):
    return client.post(
        _url(task_id=task.id),
        data={
            'task_id': task.id,
            'status': status.id,
            'notes': notes,
        },
    )


def test__post__requires_login(client):
    assert__requires_login(client, _url(external=False, task_id=1), post=True)


def test__my_jobs__update_status(client, faker, loggedin_user):
    s = faker.service().get(save=True, owners=[loggedin_user])
    task = faker.task().get(save=True, service=s)

    st = TaskStatusType.get_in_progress()
    notes = faker.pystr(min_chars=5, max_chars=10)

    resp = _update_status_post(client, task, st, notes)

    assert  len(db.session.execute(select(TaskStatus).where(TaskStatus.task_id == task.id)).scalars().all()) == 1
    ts = db.session.execute(select(TaskStatus).where(TaskStatus.task_id == task.id)).scalars().one()
    assert ts.task_status_type_id == st.id
    assert ts.task_id == task.id
    assert ts.notes == notes


def test__my_jobs__update_status__not_owner(client, faker, loggedin_user):
    user2 = faker.user().get(save=True)

    s = faker.service().get(save=True, owners=[user2])
    task = faker.task().get(save=True, service=s)

    st = TaskStatusType.get_in_progress()
    notes = faker.pystr(min_chars=5, max_chars=10)

    resp = _update_status_post(client, task, st, notes)
    assert resp.status_code == http.HTTPStatus.FORBIDDEN
