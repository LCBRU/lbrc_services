import pytest
import re
from itertools import repeat
from lbrc_flask.database import db
from lbrc_flask.pytest.helpers import login
from lbrc_requests.model import RequestStatusType
from tests import _get_test_user


@pytest.mark.parametrize(
    ["mine", "others"],
    [(0, 0), (0, 1), (0, 0), (2, 2), (3, 0)],
)
def test__my_requests(client, faker, mine, others):
    user = login(client, faker)
    user2 = _get_test_user(faker)

    my_requests = [faker.request_details(requestor=u) for u in repeat(user, mine)]
    db.session.add_all(my_requests)
    db.session.add_all([faker.request_details(requestor=u) for u in repeat(user2, others)])
    db.session.commit()

    resp = client.get("/my_requests")

    assert_results(resp, my_requests)


def test__my_requests__search__name(client, faker):
    user = login(client, faker)

    matching = faker.request_details(requestor=user, name='Mary')
    db.session.add(matching)
    db.session.add(faker.request_details(requestor=user, name='Joseph'))
    db.session.commit()

    resp = client.get("/my_requests?search=ar")

    assert_results(resp, [matching])


def test__my_requests__search__request_status_type(client, faker):
    user = login(client, faker)

    matching = faker.request_details(requestor=user, current_status_type=RequestStatusType.get_done())
    db.session.add(matching)
    db.session.add(faker.request_details(requestor=user, current_status_type=RequestStatusType.get_awaiting_information()))
    db.session.commit()

    resp = client.get("/my_requests?request_status_type_id={}".format(RequestStatusType.get_done().id))

    assert_results(resp, [matching])


def test__my_requests__search__request_type(client, faker):
    user = login(client, faker)

    matching = faker.request_details(requestor=user)
    db.session.add(matching)
    db.session.add(faker.request_details(requestor=user))
    db.session.commit()

    resp = client.get("/my_requests?request_type_id={}".format(matching.request_type.id))

    assert_results(resp, [matching])


def assert_results(resp, matches):
    assert resp.status_code == 200
    assert len(resp.soup.find_all("li", "list-group-item")) == len(matches)

    for u, li in zip(reversed(matches), resp.soup.find_all("li", "list-group-item")):
        request_matches_li(u, li)


def request_matches_li(request, li):
    assert li.find("h1").find(string=re.compile(request.request_type.name)) is not None
    assert li.find("h1").find(string=re.compile(request.name)) is not None
    assert li.find("h2").find(string=re.compile(request.requestor.full_name)) is not None
    assert li.find("span", 'badge').find(string=re.compile(request.current_status_type.name)) is not None
