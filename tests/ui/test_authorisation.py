import pytest
from unittest.mock import patch
from lbrc_flask.pytest.helpers import login
from lbrc_flask.database import db


def _create_request_file(faker, owner, requestor):
    rt = faker.request_type_details()
    rt.owners.append(owner)
    r = faker.request_details(request_type=rt, requestor=requestor)
    rf = faker.request_file_details(request=r)
    db.session.add(rf)
    db.session.add(rt)
    db.session.add(r)
    db.session.commit()

    return rf


# must_be_request_file_owner_or_requestor

@pytest.yield_fixture(scope="function")
def mock_send_file(app):
    with patch('lbrc_requests.ui.send_file') as m:
        m.return_value = ''
        yield m


@pytest.mark.parametrize(
    "path", [
        ("/request/{}/file/{}"),
    ],
)
def test__must_be_request_file_owner_or_requestor__is_owner(client, path, faker, mock_send_file):
    user = login(client, faker)

    rf = _create_request_file(faker, owner=user, requestor=faker.user_details())

    resp = client.get(path.format(rf.request.id, rf.id))
    assert resp.status_code == 200


@pytest.mark.parametrize(
    "path", [
        ("/request/{}/file/{}"),
    ],
)
def test__must_be_request_file_owner_or_requestor__is_requestor(client, path, faker, mock_send_file):
    user = login(client, faker)

    rf = _create_request_file(faker, owner=faker.user_details(), requestor=user)

    resp = client.get(path.format(rf.request.id, rf.id))
    assert resp.status_code == 200


@pytest.mark.parametrize(
    "path", [
        ("/request/{}/file/{}"),
    ],
)
def test__must_be_request_file_owner_or_requestor__is_neither(client, path, faker):
    user = login(client, faker)

    rf = _create_request_file(faker, owner=faker.user_details(), requestor=faker.user_details())

    resp = client.get(path.format(rf.request.id, rf.id))
    assert resp.status_code == 403


@pytest.mark.parametrize(
    "path", [
        ("/request/{}/file/{}"),
    ],
)
def test__request_not_found(client, path, faker):
    user = login(client, faker)

    rf = _create_request_file(faker, owner=faker.user_details(), requestor=faker.user_details())

    resp = client.get(path.format(rf.request.id + 1, rf.id + 1))
    assert resp.status_code == 404
