import pytest
import re
from flask import url_for
from lbrc_services.model import TaskStatusType
from tests import get_test_task, get_test_user
from lbrc_flask.pytest.asserts import assert__html_standards, assert__requires_login


def _url(external=True, **kwargs):
    return url_for('ui.my_requests', _external=external, **kwargs)


def test__get__requires_login(client):
    assert__requires_login(client, _url(external=False))


def test__standards(client, faker):
    assert__html_standards(client, faker, _url())


@pytest.mark.parametrize(
    ["mine", "others"],
    [(0, 0), (0, 1), (0, 0), (2, 2), (3, 0)],
)
def test__my_requests(client, faker, mine, others, loggedin_user):
    user2 = get_test_user(faker)

    my_requests = [get_test_task(faker, requestor=loggedin_user) for _ in range(mine)]
    not_my_requests = [get_test_task(faker, requestor=user2) for _ in range(others)]

    resp = client.get(_url())

    assert_results(resp, my_requests)


def test__my_requests__search__name(client, faker, loggedin_user):
    matching = get_test_task(faker, requestor=loggedin_user, name='Mary')
    non_matching = get_test_task(faker, requestor=loggedin_user, name='Joseph')

    resp = client.get(_url(search='ar'))

    assert_results(resp, [matching])


def test__my_requests__search__task_status_type(client, faker, loggedin_user):
    matching = get_test_task(faker, requestor=loggedin_user, current_status_type=TaskStatusType.get_done())
    non_matching = get_test_task(faker, requestor=loggedin_user, current_status_type=TaskStatusType.get_awaiting_information())

    resp = client.get(_url(task_status_type_id=TaskStatusType.get_done().id))

    assert_results(resp, [matching])


def test__my_requests__search__service(client, faker, loggedin_user):
    matching = get_test_task(faker, requestor=loggedin_user)
    non_matching = get_test_task(faker, requestor=loggedin_user)

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
