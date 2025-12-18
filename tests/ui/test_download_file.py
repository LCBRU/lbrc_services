import pytest
import http
from lbrc_flask.pytest.asserts import assert__requires_login
from unittest.mock import patch
from flask import url_for


def _url(task_file_id, task_id, external=True):
    return url_for('ui.download_task_file', task_id=task_id, task_file_id=task_file_id, _external=external)


@pytest.fixture(scope="function")
def mock_send_file(app):
    with patch('lbrc_services.ui.views.task.send_file') as m:
        m.return_value = ''
        yield m


def test_url_requires_login_get(client, faker):
    tf = faker.task_file().get_in_db()
    assert__requires_login(client, _url(tf.id, tf.task.id, external=False))


def test__must_be_task_file_owner_or_requestor__is_owner(client, faker, mock_send_file, loggedin_user):
    s = faker.service().get_in_db(owners=[loggedin_user])
    t = faker.task().get_in_db(service=s)
    tf = faker.task_file().get_in_db(task=t)

    resp = client.get(_url(tf.id, tf.task.id))
    assert resp.status_code == http.HTTPStatus.OK


def test__must_be_task_file_owner_or_requestor__is_requestor(client, faker, mock_send_file, loggedin_user):
    t = faker.task().get_in_db(requestor=loggedin_user)
    tf = faker.task_file().get_in_db(task=t)

    resp = client.get(_url(tf.id, tf.task.id))
    assert resp.status_code == http.HTTPStatus.OK


def test__must_be_task_file_owner_or_requestor__is_neither(client, faker, loggedin_user):
    tf = faker.task_file().get_in_db()
    resp = client.get(_url(tf.id, tf.task.id))
    assert resp.status_code == http.HTTPStatus.FORBIDDEN


def test__task_file__not_found(client, faker, mock_send_file, loggedin_user):
    s = faker.service().get_in_db(owners=[loggedin_user])
    t = faker.task().get_in_db(service=s)
    tf = faker.task_file().get_in_db(task=t)

    resp = client.get(_url(999, tf.task.id))

    assert resp.status_code == http.HTTPStatus.NOT_FOUND


def test__task__not_found(client, faker, mock_send_file, loggedin_user):
    s = faker.service().get_in_db(owners=[loggedin_user])
    t = faker.task().get_in_db(service=s)
    tf = faker.task_file().get_in_db(task=t)

    resp = client.get(_url(tf.id, 999))

    assert resp.status_code == http.HTTPStatus.NOT_FOUND
