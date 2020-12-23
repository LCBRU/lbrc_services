import pytest
import re
from flask import url_for
from itertools import repeat
from lbrc_flask.database import db
from lbrc_flask.pytest.helpers import login
from lbrc_requests.model import RequestStatusType
from tests import get_test_user
from lbrc_flask.pytest.asserts import assert__form_standards, assert__html_standards


def _url(**kwargs):
    return url_for('ui.my_jobs', _external=True, **kwargs)


def test__get__requires_login(client):
    resp = client.get(_url())
    assert resp.status_code == 302


@pytest.mark.app_crsf(True)
def test__standards(client, faker):
    assert__html_standards(client, faker, _url())
    assert__form_standards(client, faker, _url())


@pytest.mark.parametrize(
    ["mine", "others"],
    [(0, 0), (0, 1), (0, 0), (2, 2), (3, 0)],
)
def test__my_jobs(client, faker, mine, others):
    user = login(client, faker)
    user2 = get_test_user(faker)
    rt1 = faker.request_type_details(owners=[user])
    rt2 = faker.request_type_details(owners=[user2])

    my_jobs = [faker.request_details(request_type=rt) for rt in repeat(rt1, mine)]
    db.session.add_all(my_jobs)
    db.session.add_all([faker.request_details(request_type=rt) for rt in repeat(rt2, others)])
    db.session.commit()

    resp = client.get(_url())

    assert_results(resp, my_jobs)


def test__my_jobs__search__name(client, faker):
    user = login(client, faker)
    rt = faker.request_type_details(owners=[user])

    matching = faker.request_details(request_type=rt, name='Mary')
    db.session.add(matching)
    db.session.add(faker.request_details(request_type=rt, name='Joseph'))
    db.session.commit()

    resp = client.get(_url(search='ar'))

    assert_results(resp, [matching])


def test__my_jobs__search__request_status_type(client, faker):
    user = login(client, faker)
    rt = faker.request_type_details(owners=[user])

    matching = faker.request_details(request_type=rt, current_status_type=RequestStatusType.get_done())
    db.session.add(matching)
    db.session.add(faker.request_details(request_type=rt, current_status_type=RequestStatusType.get_awaiting_information()))
    db.session.commit()

    resp = client.get(_url(request_status_type_id=RequestStatusType.get_done().id))

    assert_results(resp, [matching])


def test__my_jobs__search__request_type(client, faker):
    user = login(client, faker)
    rt1 = faker.request_type_details(owners=[user])
    rt2 = faker.request_type_details(owners=[user])

    matching = faker.request_details(request_type=rt1)
    db.session.add(matching)
    db.session.add(faker.request_details(request_type=rt2))
    db.session.commit()

    resp = client.get(_url(request_type_id=matching.request_type.id))

    assert_results(resp, [matching])


def test__my_jobs__search__requestor(client, faker):
    user = login(client, faker)
    rt = faker.request_type_details(owners=[user])

    matching = faker.request_details(request_type=rt)
    db.session.add(matching)
    db.session.add(faker.request_details(request_type=rt))
    db.session.commit()

    resp = client.get(_url(requestor_id=matching.requestor.id))

    assert_results(resp, [matching])


def test__my_jobs__update_status(client, faker):
    user = login(client, faker)
    rt = faker.request_type_details(owners=[user])

    matching = faker.request_details(request_type=rt)
    db.session.add(matching)
    db.session.add(faker.request_details(request_type=rt))
    db.session.commit()

    resp = client.get(_url(requestor_id=matching.requestor.id))

    assert_results(resp, [matching])


def assert_results(resp, matches):
    assert resp.status_code == 200
    assert len(resp.soup.find_all("li", "list-group-item")) == len(matches)

    for u, li in zip(matches, resp.soup.find_all("li", "list-group-item")):
        request_matches_li(u, li)


def request_matches_li(request, li):
    assert li.find("h1").find(string=re.compile(request.request_type.name)) is not None
    assert li.find("h1").find(string=re.compile(request.name)) is not None
    assert li.find("h2").find(string=re.compile(request.requestor.full_name)) is not None
    assert li.find("button", "btn").find(string=re.compile(request.current_status_type.name)) is not None
