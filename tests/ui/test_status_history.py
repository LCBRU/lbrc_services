import re
from lbrc_flask.pytest.asserts import assert__requires_login
import pytest
from itertools import cycle
from lbrc_services.model import TaskStatus, TaskStatusType
from flask import url_for
from lbrc_flask.database import db
from tests import get_test_owned_task, get_test_task, get_test_user


def _url(external=True, **kwargs):
    return url_for('ui.task_status_history', _external=external, **kwargs)


def test__get__requires_login(client, faker):
    task = get_test_task(faker)
    assert__requires_login(client, _url(task_id=task.id, external=False))


def test__status_history__not_owner_or_requestor(client, faker, loggedin_user):
    user2 = get_test_user(faker)
    task = get_test_owned_task(faker, owner=user2)

    resp = client.get(_url(task_id=task.id))

    assert resp.status_code == 403


def test__status_history__missing(client, faker, loggedin_user):
    task = get_test_owned_task(faker, owner=loggedin_user)

    resp = client.get(_url(task_id=task.id + 1))

    assert resp.status_code == 404


def test__status_history__is_owner(client, faker, loggedin_user):
    task = get_test_owned_task(faker, owner=loggedin_user)

    resp = client.get(_url(task_id=task.id))

    assert resp.status_code == 200


def test__status_history__is_requestor(client, faker, loggedin_user):
    task = get_test_task(faker, requestor=loggedin_user)

    resp = client.get(_url(task_id=task.id))

    assert resp.status_code == 200


@pytest.mark.parametrize(
    ["n"],
    [(0,), (1,), (2,), (10,)],
)
def test__my_jobs__update_status(client, faker, n, loggedin_user):
    actual_status = TaskStatusType.get_created()
    task = get_test_owned_task(faker, owner=loggedin_user, current_status_type=actual_status)

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

        assert resp.status_code == 200
        assert len(resp.soup.find_all("li", "list-group-item")) == len(history)

        for h, li in zip(reversed(history), resp.soup.find_all("li", "list-group-item")):
            assert li.find("h1").find(string=re.compile(h['status'].name)) is not None
            assert li.find("p").find(string=re.compile(h['notes'])) is not None
