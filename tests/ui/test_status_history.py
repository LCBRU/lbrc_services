import re
import pytest
import http
from lbrc_flask.pytest.asserts import assert__requires_login
from itertools import cycle
from lbrc_services.model.services import TaskStatus, TaskStatusType
from flask import url_for
from lbrc_flask.database import db


def _url(external=True, **kwargs):
    return url_for('ui.task_status_history', _external=external, **kwargs)


def test__get__requires_login(client, faker):
    task = faker.task().get_in_db()
    assert__requires_login(client, _url(task_id=task.id, external=False))


def test__status_history__not_owner_or_requestor(client, faker, loggedin_user):
    user2 = faker.user().get_in_db()
    s = faker.service().get_in_db(owners=[user2])
    task = faker.task().get_in_db(service=s)

    resp = client.get(_url(task_id=task.id))

    assert resp.status_code == http.HTTPStatus.FORBIDDEN


def test__status_history__missing(client, faker, loggedin_user):
    s = faker.service().get_in_db(owners=[loggedin_user])
    task = faker.task().get_in_db(service=s)

    resp = client.get(_url(task_id=task.id + 1))

    assert resp.status_code == http.HTTPStatus.NOT_FOUND


def test__status_history__is_owner(client, faker, loggedin_user):
    s = faker.service().get_in_db(owners=[loggedin_user])
    task = faker.task().get_in_db(service=s)
    
    resp = client.get(_url(task_id=task.id))

    assert resp.status_code == http.HTTPStatus.OK


def test__status_history__is_requestor(client, faker, loggedin_user):
    task = faker.task().get_in_db(requestor=loggedin_user)

    resp = client.get(_url(task_id=task.id))

    assert resp.status_code == http.HTTPStatus.OK


@pytest.mark.parametrize(
    ["n"],
    [(0,), (1,), (2,), (10,)],
)
def test__my_jobs__update_status(client, faker, n, loggedin_user):
    actual_status = TaskStatusType.get_created()
    s = faker.service().get_in_db(owners=[loggedin_user])
    task = faker.task().get_in_db(service=s, current_status_type=actual_status)

    statuses = cycle(TaskStatusType.query.all())
    history = []

    for x in range(n):
        history.append({
            'status': next(statuses),
            'notes': faker.pystr(min_chars=5, max_chars=10),
        })
        task.status_history.append(TaskStatus(
            task=task,
            notes=history[-1]['notes'],
            task_status_type=history[-1]['status']
        ))

        db.session.add(task)
        db.session.commit()

        resp = client.get(_url(task_id=task.id))

        print(resp.soup)

        assert resp.status_code == http.HTTPStatus.OK
        assert len(resp.soup.select("table tbody tr")) == len(history)

        for h, tr in zip(reversed(history), resp.soup.select("table tbody tr")):
            assert tr.find(string=re.compile(h['status'].name)) is not None
            assert tr.find(string=re.compile(h['notes'])) is not None
