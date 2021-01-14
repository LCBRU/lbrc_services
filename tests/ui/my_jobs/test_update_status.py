from itertools import cycle
import pytest
from tests import get_test_user, get_test_task
from lbrc_services.model import TaskStatusType, Task
from flask import url_for
from lbrc_flask.pytest.helpers import login
from lbrc_flask.pytest.asserts import assert__form_standards, assert__html_standards


def _url(**kwargs):
    return url_for('ui.my_jobs', _external=True, **kwargs)


def test__post__requires_login(client):
    resp = client.post(_url())
    assert resp.status_code == 302


@pytest.mark.app_crsf(True)
def test__standards(client, faker):
    assert__html_standards(client, faker, _url())
    assert__form_standards(client, faker, _url())


def _post_update_task_status(client, faker, task_id, status_type_id, notes):
    return client.post(
        _url(),
        data = {
            'task_id': task_id,
            'status': status_type_id,
            'notes': notes,
        },
    )


@pytest.mark.parametrize(
    ["n"],
    [(0,), (1,), (2,), (10,)],
)
def test__my_jobs__update_status(client, faker, n):
    user = login(client, faker)
    s = faker.service_details(owners=[user])

    actual_status = TaskStatusType.get_created()
    task = get_test_task(faker, service=s, current_status_type=actual_status)

    statuses = cycle(TaskStatusType.query.all())
    history = []

    for x in range(n):
        history.append({
            'status': next(statuses),
            'notes': faker.pystr(min_chars=5, max_chars=10),
        })
        resp = _post_update_task_status(
            client,
            faker,
            task.id,
            history[-1]['status'].id,
            history[-1]['notes'],
        )

        assert resp.status_code == 302
        assert resp.location == _url()

        actual = Task.query.get(task.id)
        assert actual.current_status_type == history[-1]['status']
        assert len(actual.status_history) == len(history)

        for e, a in zip(history, actual.status_history):
            assert e['status'] == a.task_status_type
            assert e['notes'] == a.notes


def test__my_jobs__update_status__not_owner(client, faker):
    user1 = login(client, faker)
    user2 = get_test_user(faker)
    s = faker.service_details(owners=[user2])

    task = get_test_task(faker, service=s, current_status_type=TaskStatusType.get_created())

    resp = _post_update_task_status(client, faker, task.id, TaskStatusType.get_done().id, faker.pystr(min_chars=5, max_chars=10))

    assert resp.status_code == 403


def test__my_jobs__update_status__not_owner(client, faker):
    user = login(client, faker)

    resp = _post_update_task_status(client, faker, 999, TaskStatusType.get_done().id, faker.pystr(min_chars=5, max_chars=10))

    assert resp.status_code == 404
