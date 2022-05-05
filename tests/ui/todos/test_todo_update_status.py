from flask import url_for
from flask_api import status
import pytest
from lbrc_services.model import ToDo
from lbrc_flask.pytest.asserts import assert__requires_login


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


@pytest.mark.skip(reason="Flask_Login is adding extra parameters to URL")
def test__post__requires_login(client, faker):
    assert__requires_login(client, _url(external=False), post=True)


def test__post__missing(client, faker, loggedin_user):
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
def test__update_todo_status__correct_values(client, faker, starting_status, action, expect_status, loggedin_user):
    todo = faker.get_test_owned_todo(loggedin_user, status_name=starting_status)

    resp = _update_status_post(client, todo_id=todo.id, action=action)
    assert resp.status_code == status.HTTP_205_RESET_CONTENT

    actual = ToDo.query.get(todo.id)

    assert actual.status == ToDo.get_status_code_from_name(expect_status)

def test__update_todo_status__invalid_action(client, faker, loggedin_user):
    todo = faker.get_test_owned_todo(loggedin_user, status_name=ToDo.OUTSTANDING)

    resp = _update_status_post(client, todo_id=todo.id, action='This is not correct')
    assert resp.status_code == status.HTTP_400_BAD_REQUEST

    actual = ToDo.query.get(todo.id)
    assert actual.status == ToDo.get_status_code_from_name(ToDo.OUTSTANDING)


def test__update_todo_status__not_owner(client, faker, loggedin_user):
    todo = faker.get_test_todo()

    resp = _update_status_post(client, todo_id=todo.id, action='check')
    assert resp.status_code == status.HTTP_403_FORBIDDEN
