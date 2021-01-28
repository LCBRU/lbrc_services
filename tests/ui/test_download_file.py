from lbrc_flask.pytest.asserts import assert__requires_login
import pytest
from unittest.mock import patch
from tests import get_test_owned_task, get_test_task, get_test_task_file, get_test_service
from flask import url_for
from flask_api import status


def _url(task_file_id, task_id, external=True):
    return url_for('ui.download_task_file', task_id=task_id, task_file_id=task_file_id, _external=external)


@pytest.fixture(scope="function")
def mock_send_file(app):
    with patch('lbrc_services.ui.send_file') as m:
        m.return_value = ''
        yield m


def test_url_requires_login_get(client, faker):
    tf = get_test_task_file(faker)
    assert__requires_login(client, _url(tf.id, tf.task.id, external=False))


def test__must_be_task_file_owner_or_requestor__is_owner(client, faker, mock_send_file, loggedin_user):
    t = get_test_owned_task(faker, owner=loggedin_user)
    tf = get_test_task_file(faker, task=t)

    resp = client.get(_url(tf.id, tf.task.id))
    assert resp.status_code == status.HTTP_200_OK


def test__must_be_task_file_owner_or_requestor__is_requestor(client, faker, mock_send_file, loggedin_user):
    t = get_test_task(faker, requestor=loggedin_user)
    tf = get_test_task_file(faker, task=t)

    resp = client.get(_url(tf.id, tf.task.id))
    assert resp.status_code == status.HTTP_200_OK


def test__must_be_task_file_owner_or_requestor__is_neither(client, faker, loggedin_user):
    tf = get_test_task_file(faker)
    resp = client.get(_url(tf.id, tf.task.id))
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test__task_file__not_found(client, faker, mock_send_file, loggedin_user):
    t = get_test_owned_task(faker, owner=loggedin_user)
    tf = get_test_task_file(faker, task=t)

    resp = client.get(_url(999, tf.task.id))

    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test__task__not_found(client, faker, mock_send_file, loggedin_user):
    t = get_test_owned_task(faker, owner=loggedin_user)
    tf = get_test_task_file(faker, task=t)

    resp = client.get(_url(tf.id, 999))

    assert resp.status_code == status.HTTP_404_NOT_FOUND
