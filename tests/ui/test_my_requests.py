import pytest
import re
from flask import url_for
from itertools import repeat
from lbrc_flask.database import db
from lbrc_flask.pytest.helpers import login
from lbrc_services.model import TaskStatusType
from tests import get_test_user
from lbrc_flask.pytest.asserts import assert__html_standards


def _url(**kwargs):
    return url_for('ui.my_requests', _external=True, **kwargs)


def test__get__requires_login(client):
    resp = client.get(_url())
    assert resp.status_code == 302


def test__standards(client, faker):
    assert__html_standards(client, faker, _url())


@pytest.mark.parametrize(
    ["mine", "others"],
    [(0, 0), (0, 1), (0, 0), (2, 2), (3, 0)],
)
def test__my_requests(client, faker, mine, others):
    user = login(client, faker)
    user2 = get_test_user(faker)

    my_requests = [faker.task_details(requestor=u) for u in repeat(user, mine)]
    db.session.add_all(my_requests)
    db.session.add_all([faker.task_details(requestor=u) for u in repeat(user2, others)])
    db.session.commit()

    resp = client.get(_url())

    assert_results(resp, my_requests)


def test__my_requests__search__name(client, faker):
    user = login(client, faker)

    matching = faker.task_details(requestor=user, name='Mary')
    db.session.add(matching)
    db.session.add(faker.task_details(requestor=user, name='Joseph'))
    db.session.commit()

    resp = client.get(_url(search='ar'))

    assert_results(resp, [matching])


def test__my_requests__search__task_status_type(client, faker):
    user = login(client, faker)

    matching = faker.task_details(requestor=user, current_status_type=TaskStatusType.get_done())
    db.session.add(matching)
    db.session.add(faker.task_details(requestor=user, current_status_type=TaskStatusType.get_awaiting_information()))
    db.session.commit()

    resp = client.get(_url(task_status_type_id=TaskStatusType.get_done().id))

    assert_results(resp, [matching])


def test__my_requests__search__service(client, faker):
    user = login(client, faker)

    matching = faker.task_details(requestor=user)
    db.session.add(matching)
    db.session.add(faker.task_details(requestor=user))
    db.session.commit()

    resp = client.get(_url(service_id=matching.service.id))

    assert_results(resp, [matching])


def assert_results(resp, matches):
    assert resp.status_code == 200
    assert len(resp.soup.find_all("li", "list-group-item")) == len(matches)

    for u, li in zip(reversed(matches), resp.soup.find_all("li", "list-group-item")):
        task_matches_li(u, li)


def task_matches_li(task, li):
    assert li.find("h1").find(string=re.compile(task.service.name)) is not None
    assert li.find("h1").find(string=re.compile(task.name)) is not None
    assert li.find("h2").find(string=re.compile(task.requestor.full_name)) is not None
    assert li.find("a", string=re.compile(task.current_status_type.name)) is not None
