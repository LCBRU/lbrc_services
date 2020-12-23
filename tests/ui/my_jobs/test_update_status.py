from itertools import cycle
import pytest
from tests import get_test_user, get_test_request
from lbrc_requests.model import RequestStatusType, Request
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


def _post_update_request_status(client, faker, request, status_type_id, notes):
    return client.post(
        _url(),
        data = {
            'request_id': request.id,
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
        resp = _post_update_request_status(
            client,
            faker,
            request,
            history[-1]['status'].id,
            history[-1]['notes'],
        )

        assert resp.status_code == 302
        assert resp.location == _url()

        actual = Request.query.get(request.id)
        assert actual.current_status_type == history[-1]['status']
        assert len(actual.status_history) == len(history)

        for e, a in zip(history, actual.status_history):
            assert e['status'] == a.request_status_type
            assert e['notes'] == a.notes


def test__my_jobs__update_status__not_owner(client, faker):
    user1 = login(client, faker)
    user2 = get_test_user(faker)
    rt = faker.request_type_details(owners=[user2])

    request = get_test_request(faker, request_type=rt, current_status_type=RequestStatusType.get_created())

    resp = _post_update_request_status(client, faker, request, RequestStatusType.get_done().id, faker.pystr(min_chars=5, max_chars=10))

    assert resp.status_code == 403
