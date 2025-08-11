import pytest
import http
from flask import url_for
from lbrc_services.model.services import ToDo
from lbrc_flask.database import db
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


def test__post__requires_login(client, faker):
    assert__requires_login(client, _url(external=False), post=True)


def test__post__missing(client, faker, loggedin_user):
    resp = _update_status_post(client, todo_id=9999, action='check')
    assert resp.status_code == http.HTTPStatus.NOT_FOUND


@pytest.mark.parametrize(
    ["starting_status", "action", "expect_status"],
    [
        (ToDo.OUTSTANDING_NAME, 'check', ToDo.COMPLETED_NAME),
        (ToDo.COMPLETED_NAME, 'unneeded', ToDo.NOT_REQUIRED_NAME),
        (ToDo.NOT_REQUIRED_NAME, 'uncheck', ToDo.OUTSTANDING_NAME),
        (ToDo.OUTSTANDING_NAME, 'unneeded', ToDo.NOT_REQUIRED_NAME),
        (ToDo.COMPLETED_NAME, 'uncheck', ToDo.OUTSTANDING_NAME),
        (ToDo.NOT_REQUIRED_NAME, 'check', ToDo.COMPLETED_NAME),
    ],
)
def test__update_todo_status__correct_values(client, faker, starting_status, action, expect_status, loggedin_user):
    todo = faker.get_test_owned_todo(loggedin_user, status_name=starting_status)

    resp = _update_status_post(client, todo_id=todo.id, action=action)
    assert resp.status_code == http.HTTPStatus.RESET_CONTENT

    actual = db.session.get(ToDo, todo.id)

    assert actual.status == ToDo.get_status_code_from_name(expect_status)

def test__update_todo_status__invalid_action(client, faker, loggedin_user):
    todo = faker.get_test_owned_todo(loggedin_user, status_name=ToDo.OUTSTANDING_NAME)

    resp = _update_status_post(client, todo_id=todo.id, action='This is not correct')
    assert resp.status_code == http.HTTPStatus.BAD_REQUEST

    actual = db.session.get(ToDo, todo.id)
    assert actual.status == ToDo.get_status_code_from_name(ToDo.OUTSTANDING_NAME)


def test__update_todo_status__not_owner(client, faker, loggedin_user):
    todo = faker.get_test_todo()

    resp = _update_status_post(client, todo_id=todo.id, action='check')
    assert resp.status_code == http.HTTPStatus.FORBIDDEN
