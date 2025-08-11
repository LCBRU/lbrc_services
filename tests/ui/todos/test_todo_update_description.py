import http
from flask import url_for
from lbrc_services.model.services import ToDo
from lbrc_flask.pytest.asserts import assert__redirect, assert__requires_login
from lbrc_flask.database import db


def _url(external=True):
    return url_for('ui.task_save_todo', _external=external)


def _update_todo_post(client, task_id, todo_id, description):
    return client.post(
        _url(external=False),
        data={
            'task_id': task_id,
            'todo_id': todo_id,
            'description': description,
        },
    )


def _create_todo_post(client, task_id, description, prev=None):
    prev = prev or _url()
    
    return client.post(
        _url(external=False),
        data={
            'task_id': task_id,
            'description': description,
            'prev': prev,
        },
    )


def test__post__requires_login(client, faker):
    assert__requires_login(client, _url(external=False), post=True)


def test__update_post__todo_missing(client, faker, loggedin_user):
    task = faker.get_test_owned_task(owner=loggedin_user)

    resp = _update_todo_post(client, task_id=task.id, todo_id=9999, description=faker.pystr(min_chars=5, max_chars=100))
    assert resp.status_code == http.HTTPStatus.NOT_FOUND


def test__create_post__task_missing(client, faker, loggedin_user):
    resp = _create_todo_post(client, task_id=9999, description=faker.pystr(min_chars=5, max_chars=100))
    assert resp.status_code == http.HTTPStatus.NOT_FOUND


def test__create_post__ok(client, faker, loggedin_user):
    task = faker.get_test_owned_task(owner=loggedin_user)

    expected = faker.pystr(min_chars=5, max_chars=100)

    resp = _create_todo_post(client, task_id=task.id, description=expected, prev=_url())
    assert__redirect(resp, endpoint='ui.task_todo_list', task_id=task.id, prev=_url())

    ToDo.query.count() == 1
    actual = ToDo.query.one()
    assert actual.task_id == task.id
    assert actual.description == expected
    assert actual.status == ToDo.get_status_code_from_name(ToDo.OUTSTANDING_NAME)


def test__update_post__ok(client, faker, loggedin_user):
    todo = faker.get_test_owned_todo(loggedin_user)

    expected = faker.pystr(min_chars=5, max_chars=100)

    resp = _update_todo_post(client, task_id=todo.task.id, todo_id=todo.id, description=expected)
    assert__redirect(resp, endpoint='ui.task_todo_list', task_id=todo.task.id)

    ToDo.query.count() == 1
    actual = ToDo.query.one()
    assert actual.id == todo.id
    assert actual.description == expected
    assert actual.status == ToDo.get_status_code_from_name(ToDo.OUTSTANDING_NAME)


def test__update_post__not_owner(client, faker, loggedin_user):
    user2 = faker.get_test_user()

    s = faker.service_details(owners=[user2])
    db.session.add(s)
    task = faker.get_test_task(service=s)
    todo = faker.get_test_todo(task=task)
    db.session.commit()

    expected = faker.pystr(min_chars=5, max_chars=100)

    resp = _update_todo_post(client, task_id=todo.task.id, todo_id=todo.id, description=expected)
    assert resp.status_code == http.HTTPStatus.FORBIDDEN
