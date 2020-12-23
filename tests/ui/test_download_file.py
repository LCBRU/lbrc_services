import pytest
from unittest.mock import patch
from tests import get_test_request, get_test_request_file, get_test_request_type
from lbrc_flask.pytest.helpers import login
from flask import url_for


def _url(request_file_id, request_id):
    return url_for('ui.download_request_file', request_id=request_id, request_file_id=request_file_id, _external=True)


@pytest.yield_fixture(scope="function")
def mock_send_file(app):
    with patch('lbrc_requests.ui.send_file') as m:
        m.return_value = ''
        yield m


def test_url_requires_login_get(client, faker):
    rf = get_test_request_file(faker)
    resp = client.get(_url(rf.id, rf.request.id))
    assert resp.status_code == 302


def test__must_be_request_file_owner_or_requestor__is_owner(client, faker, mock_send_file):
    user = login(client, faker)

    rt = get_test_request_type(faker, owners=[user])
    r = get_test_request(faker, request_type=rt)
    rf = get_test_request_file(faker, request=r)

    resp = client.get(_url(rf.id, rf.request.id))
    assert resp.status_code == 200


def test__must_be_request_file_owner_or_requestor__is_requestor(client, faker, mock_send_file):
    user = login(client, faker)

    r = get_test_request(faker, requestor=user)
    rf = get_test_request_file(faker, request=r)

    resp = client.get(_url(rf.id, rf.request.id))
    assert resp.status_code == 200


def test__must_be_request_file_owner_or_requestor__is_neither(client, faker):
    user = login(client, faker)

    rf = get_test_request_file(faker)
    resp = client.get(_url(rf.id, rf.request.id))
    assert resp.status_code == 403


def test__request_file__not_found(client, faker, mock_send_file):
    user = login(client, faker)

    rt = get_test_request_type(faker, owners=[user])
    r = get_test_request(faker, request_type=rt)
    rf = get_test_request_file(faker, request=r)

    resp = client.get(_url(999, rf.request.id))

    assert resp.status_code == 404


def test__request__not_found(client, faker, mock_send_file):
    user = login(client, faker)

    rt = get_test_request_type(faker, owners=[user])
    r = get_test_request(faker, request_type=rt)
    rf = get_test_request_file(faker, request=r)

    resp = client.get(_url(rf.id, 999))

    assert resp.status_code == 404
