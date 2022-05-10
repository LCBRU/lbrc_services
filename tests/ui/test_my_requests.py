import pytest
import re
from flask import url_for
from lbrc_services.model.services import TaskStatusType
from tests import lbrc_services_get
from lbrc_flask.pytest.asserts import assert__requires_login, assert__search_html, assert__select, assert__page_navigation
from flask_api import status
from lbrc_services.ui.forms import TaskSearchForm, _get_combined_task_status_type_choices, _get_service_choices
from pprint import pp


def _url(external=True, **kwargs):
    return url_for('ui.my_requests', _external=external, **kwargs)


def test__get__requires_login(client):
    assert__requires_login(client, _url(external=False))


def _get(client, url, loggedin_user, has_form):
    resp = lbrc_services_get(client, url, loggedin_user, has_form)

    assert__search_html(resp.soup, clear_url=_url(external=False))

    assert__select(soup=resp.soup, id='service_id', options=_get_service_choices())
    assert__select(soup=resp.soup, id='task_status_type_id', options=_get_combined_task_status_type_choices())

    return resp


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    ["mine", "others"],
    [(0, 0), (0, 1), (0, 0), (2, 2), (3, 0)],
)
def test__my_requests(client, faker, mine, others, loggedin_user):
    user2 = faker.get_test_user()

    my_requests = [faker.get_test_task(requestor=loggedin_user) for _ in range(mine)]
    not_my_requests = [faker.get_test_task(requestor=user2) for _ in range(others)]

    resp = _get(client, _url(), loggedin_user, has_form=True)

    for r in my_requests:
        pp(r)

    assert_results(resp, my_requests)


@pytest.mark.app_crsf(True)
def test__my_requests__search__name(client, faker, loggedin_user):
    matching = faker.get_test_task(requestor=loggedin_user, name='Mary')
    non_matching = faker.get_test_task(requestor=loggedin_user, name='Joseph')

    resp = _get(client, _url(search='ar'), loggedin_user, has_form=True)

    assert_results(resp, [matching])


@pytest.mark.app_crsf(True)
def test__my_requests__search__task_status_type(client, faker, loggedin_user):
    matching = faker.get_test_task(requestor=loggedin_user, current_status_type=TaskStatusType.get_done())
    non_matching = faker.get_test_task(requestor=loggedin_user, current_status_type=TaskStatusType.get_awaiting_information())

    resp = _get(client, _url(task_status_type_id=TaskStatusType.get_done().id), loggedin_user, has_form=True)

    assert_results(resp, [matching])


@pytest.mark.app_crsf(True)
def test__my_requests__search__service(client, faker, loggedin_user):
    matching = faker.get_test_task(requestor=loggedin_user)
    non_matching = faker.get_test_task(requestor=loggedin_user)

    resp = _get(client, _url(service_id=matching.service.id), loggedin_user, has_form=True)

    assert_results(resp, [matching])


def assert_results(resp, matches):
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.soup.find_all("li", "list-group-item")) == len(matches)

    for u, li in zip(reversed(matches), resp.soup.find_all("li", "list-group-item")):
        task_matches_li(u, li)


def task_matches_li(task, li):
    assert li.find("h1").find(string=re.compile(task.service.name)) is not None
    assert li.find("h1").find(string=re.compile(task.name)) is not None
    assert li.find("h2").find(string=re.compile(task.requestor.full_name)) is not None


@pytest.mark.parametrize(
    "jobs",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_jobs__pages(client, faker, jobs, loggedin_user):
    my_jobs = [faker.get_test_owned_task(loggedin_user, requestor=loggedin_user, count=jobs)]

    assert__page_navigation(client, 'ui.my_requests', {'_external': False}, jobs, form=TaskSearchForm())


@pytest.mark.parametrize(
    "jobs",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_jobs__search__name__pages(client, faker, jobs, loggedin_user):
    matching = [faker.get_test_owned_task(name='Mary', owner=loggedin_user, requestor=loggedin_user, count=jobs)]
    unmatching = [faker.get_test_owned_task(name='Joseph', owner=loggedin_user, requestor=loggedin_user, count=100)]

    assert__page_navigation(client, 'ui.my_requests', {'_external': False, 'search': 'ar'}, jobs, form=TaskSearchForm())


@pytest.mark.parametrize(
    "jobs",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_jobs__search__task_status__pages(client, faker, jobs, loggedin_user):
    matching = [faker.get_test_owned_task(current_status_type=TaskStatusType.get_done(), owner=loggedin_user, requestor=loggedin_user, count=jobs)]
    unmatching = [faker.get_test_owned_task(current_status_type=TaskStatusType.get_awaiting_information(), owner=loggedin_user, requestor=loggedin_user, count=100)]

    assert__page_navigation(client, 'ui.my_requests', {'_external': False, 'task_status_type_id': TaskStatusType.get_done().id}, jobs, form=TaskSearchForm())


@pytest.mark.parametrize(
    "jobs",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_jobs__search__service__pages(client, faker, jobs, loggedin_user):
    service1 = faker.get_test_service(owners=[loggedin_user])
    service2 = faker.get_test_service(owners=[loggedin_user])
    matching = [faker.get_test_task(service=service1, requestor=loggedin_user, count=jobs)]
    unmatching = [faker.get_test_task(service=service2, requestor=loggedin_user, count=100)]

    assert__page_navigation(client, 'ui.my_requests', {'_external': False, 'service_id': service1.id}, jobs, form=TaskSearchForm())
