from flask import url_for
from flask_api import status
import pytest
from tests import get_test_service, get_test_todo
from lbrc_services.model import ToDo
from lbrc_flask.pytest.asserts import assert__requires_login
from lbrc_flask.pytest.helpers import login
from lbrc_flask.database import db


def _url(external=True):
    return url_for('ui.todo_update_status', _external=external)


def _update_status_post(client, todo_id, action):
    return client.post(
        _url(external=False),
        json={
            'todo_id': todo_id,
            'action': action,
        },
    )


def test__post__requires_login(client, faker):
    s = get_test_service(faker)
    assert__requires_login(client, _url(external=False), post=True)


def test__post__missing(client, faker):
    user = login(client, faker)

    resp = _update_status_post(client, todo_id=9999, action='check')
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    ["starting_status", "action", "expect_status"],
    [
        (ToDo.OUTSTANDING, 'check', ToDo.COMPLETED),
        (ToDo.COMPLETED, 'unneeded', ToDo.NOT_REQUIRED),
        (ToDo.NOT_REQUIRED, 'uncheck', ToDo.OUTSTANDING),
        (ToDo.OUTSTANDING, 'unneeded', ToDo.NOT_REQUIRED),
        (ToDo.COMPLETED, 'uncheck', ToDo.OUTSTANDING),
        (ToDo.NOT_REQUIRED, 'check', ToDo.COMPLETED),
    ],
)
def test__update_todo_status__correct_values(client, faker, starting_status, action, expect_status):
    user = login(client, faker)

    todo = get_test_todo(faker, status=ToDo.get_status_code_from_name(starting_status))
    db.session.commit()

    resp = _update_status_post(client, todo_id=todo.id, action=action)
    assert resp.status_code == status.HTTP_205_RESET_CONTENT

    actual = ToDo.query.get(todo.id)

    assert actual.status == ToDo.get_status_code_from_name(expect_status)


def test__update_todo_status__invalid_action(client, faker):
    user = login(client, faker)

    todo = get_test_todo(faker, status=ToDo.get_status_code_from_name(ToDo.OUTSTANDING))
    db.session.commit()

    resp = _update_status_post(client, todo_id=todo.id, action='This is not correct')
    assert resp.status_code == status.HTTP_400_BAD_REQUEST

    actual = ToDo.query.get(todo.id)

    assert actual.status == ToDo.get_status_code_from_name(ToDo.OUTSTANDING)
