import re
import pytest
from itertools import cycle
from lbrc_requests.model import RequestStatus, RequestStatusType
from flask import url_for
from lbrc_flask.pytest.helpers import login
from lbrc_flask.database import db
from tests import get_test_request, get_test_user


def _url(**kwargs):
    return url_for('ui.request_status_history', _external=True, **kwargs)


def test__get__requires_login(client, faker):
    request = get_test_request(faker)
    resp = client.get(_url(request_id=request.id))
    assert resp.status_code == 302


def test__status_history__not_owner_or_requestor(client, faker):
    user1 = login(client, faker)
    user2 = get_test_user(faker)
    rt = faker.request_type_details(owners=[user2])

    request = get_test_request(faker, request_type=rt)

    resp = client.get(_url(request_id=request.id))

    assert resp.status_code == 403


def test__status_history__missing(client, faker):
    user = login(client, faker)
    rt = faker.request_type_details(owners=[user])

    request = get_test_request(faker, request_type=rt)

    resp = client.get(_url(request_id=request.id + 1))

    assert resp.status_code == 404


def test__status_history__is_owner(client, faker):
    user = login(client, faker)
    rt = faker.request_type_details(owners=[user])

    request = get_test_request(faker, request_type=rt)

    resp = client.get(_url(request_id=request.id))

    assert resp.status_code == 200


def test__status_history__is_requestor(client, faker):
    user = login(client, faker)

    request = get_test_request(faker, requestor=user)

    resp = client.get(_url(request_id=request.id))

    assert resp.status_code == 200


@pytest.mark.parametrize(
    ["n"],
    [(0,), (1,), (2,), (10,)],
)
def test__my_jobs__update_status(client, faker, n):
    user = login(client, faker)
    rt = faker.request_type_details(owners=[user])

    actual_status = RequestStatusType.get_created()
    request = get_test_request(faker, request_type=rt, current_status_type=actual_status)

    statuses = cycle(RequestStatusType.query.all())
    history = []

    for x in range(n):
        history.append({
            'status': next(statuses),
            'notes': faker.pystr(min_chars=5, max_chars=10),
        })
        request.status_history.append(RequestStatus(
            request=request,
            notes=history[-1]['notes'],
            request_status_type=history[-1]['status']
        ))

        db.session.add(request)
        db.session.commit()

        resp = client.get(_url(request_id=request.id))

        assert resp.status_code == 200
        assert len(resp.soup.find_all("li", "list-group-item")) == len(history)

        for h, li in zip(reversed(history), resp.soup.find_all("li", "list-group-item")):
            assert li.find("h1").find(string=re.compile(h['status'].name)) is not None
            assert li.find("p").find(string=re.compile(h['notes'])) is not None
