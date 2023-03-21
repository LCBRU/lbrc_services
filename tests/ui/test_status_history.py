import re
from lbrc_flask.pytest.asserts import assert__requires_login
import pytest
from itertools import cycle
from lbrc_services.model.services import TaskStatus, TaskStatusType
from flask import url_for
from lbrc_flask.database import db
from flask_api import status


def _url(external=True, **kwargs):
    return url_for('ui.task_status_history', _external=external, **kwargs)


def test__get__requires_login(client, faker):
    task = faker.get_test_task()
    assert__requires_login(client, _url(task_id=task.id, external=False))


def test__status_history__not_owner_or_requestor(client, faker, loggedin_user):
    user2 = faker.get_test_user()
    task = faker.get_test_owned_task(owner=user2)

    resp = client.get(_url(task_id=task.id))

    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test__status_history__missing(client, faker, loggedin_user):
    task = faker.get_test_owned_task(owner=loggedin_user)

    resp = client.get(_url(task_id=task.id + 1))

    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test__status_history__is_owner(client, faker, loggedin_user):
    task = faker.get_test_owned_task(owner=loggedin_user)

    resp = client.get(_url(task_id=task.id))

    assert resp.status_code == status.HTTP_200_OK


def test__status_history__is_requestor(client, faker, loggedin_user):
    task = faker.get_test_task(requestor=loggedin_user)

    resp = client.get(_url(task_id=task.id))

    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    ["n"],
    [(0,), (1,), (2,), (10,)],
)
def test__my_jobs__update_status(client, faker, n, loggedin_user):
    actual_status = TaskStatusType.get_created()
    task = faker.get_test_owned_task(owner=loggedin_user, current_status_type=actual_status)

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

        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.soup.find_all("li", "list-group-item")) == len(history)

        for h, li in zip(reversed(history), resp.soup.find_all("li", "list-group-item")):
            assert li.find("h1").find(string=re.compile(h['status'].name)) is not None
            assert li.find("p").find(string=re.compile(h['notes'])) is not None
