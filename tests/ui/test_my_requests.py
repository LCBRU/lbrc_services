import pytest
import re
import http
from flask import url_for
from lbrc_services.model.services import TaskStatusType
from tests import lbrc_services_get
from lbrc_flask.pytest.asserts import assert__requires_login, assert__search_html, assert__select, assert__page_navigation
from lbrc_services.ui.forms import TaskSearchForm, _get_combined_task_status_type_choices, _get_service_choices


def _url(external=True, **kwargs):
    return url_for('ui.my_requests', _external=external, **kwargs)


def test__get__requires_login(client):
    assert__requires_login(client, _url(external=False))


def _get(client, url, loggedin_user, has_form):
    resp = lbrc_services_get(client, url, loggedin_user, has_form)

    assert__search_html(resp.soup)

    assert__select(soup=resp.soup, id='service_id', options=dict(_get_service_choices()))
    assert__select(soup=resp.soup, id='task_status_type_id', options=dict(_get_combined_task_status_type_choices()))

    return resp


def requests_sorted_by_created_date_desc(requests):
    return sorted(requests, key=lambda r: r.created_date)

@pytest.mark.parametrize(
    ["mine", "others"],
    [(0, 0), (0, 1), (0, 0), (2, 2), (3, 0)],
)
def test__my_requests(client, faker, mine, others, loggedin_user):
    user2 = faker.user().get(save=True)

    my_requests = requests_sorted_by_created_date_desc(
        faker.task().get_list_in_db(item_count=mine, requestor=loggedin_user)
    )
    not_my_requests = faker.task().get_list_in_db(item_count=others, requestor=user2)

    resp = _get(client, _url(), loggedin_user, has_form=False)

    assert_results(resp, my_requests)


def test__my_requests__search__name(client, faker, loggedin_user):
    matching = faker.task().get(save=True, requestor=loggedin_user, name='Mary')
    non_matching = faker.task().get(save=True, requestor=loggedin_user, name='Joseph')

    resp = _get(client, _url(search='ar'), loggedin_user, has_form=False)

    assert_results(resp, [matching])


def test__my_requests__search__task_status_type(client, faker, loggedin_user):
    matching = faker.task().get(save=True, requestor=loggedin_user, current_status_type=TaskStatusType.get_done())
    non_matching = faker.task().get(save=True, requestor=loggedin_user, current_status_type=TaskStatusType.get_awaiting_information())

    resp = _get(client, _url(task_status_type_id=TaskStatusType.get_done().id), loggedin_user, has_form=False)

    assert_results(resp, [matching])


def test__my_requests__search__service(client, faker, loggedin_user):
    matching = faker.task().get(save=True, requestor=loggedin_user)
    non_matching = faker.task().get(save=True, requestor=loggedin_user)

    resp = _get(client, _url(service_id=matching.service.id), loggedin_user, has_form=False)

    assert_results(resp, [matching])


def assert_results(resp, matches):
    assert resp.status_code == http.HTTPStatus.OK
    assert len(resp.soup.select(".panel_list > li")) == len(matches)

    for u, li in zip(reversed(matches), resp.soup.select(".panel_list > li")):
        task_matches_li(u, li)


def task_matches_li(task, li):
    assert li.find("h3").find(string=re.compile(task.service.name)) is not None
    assert li.find("h3").find(string=re.compile(task.name)) is not None
    assert li.find("h4").find(string=re.compile(task.requestor.full_name)) is not None


@pytest.mark.parametrize(
    "jobs",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_jobs__pages(client, faker, jobs, loggedin_user):
    s = faker.service().get(save=True, owners=[loggedin_user])
    my_jobs = faker.task().get_list_in_db(service=s, requestor=loggedin_user, item_count=jobs)

    assert__page_navigation(client, 'ui.my_requests', {'_external': False}, jobs, form=TaskSearchForm(), page_size=10)


@pytest.mark.parametrize(
    "jobs",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_jobs__search__name__pages(client, faker, jobs, loggedin_user):
    s = faker.service().get(save=True, owners=[loggedin_user])
    matching = faker.task().get_list_in_db(service=s, name='Mary', requestor=loggedin_user, item_count=jobs)
    unmatching = faker.task().get_list_in_db(service=s, name='Joseph', requestor=loggedin_user, item_count=100)

    assert__page_navigation(client, 'ui.my_requests', {'_external': False, 'search': 'ar'}, jobs, form=TaskSearchForm(), page_size=10)


@pytest.mark.parametrize(
    "jobs",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_jobs__search__task_status__pages(client, faker, jobs, loggedin_user):
    s = faker.service().get(save=True, owners=[loggedin_user])
    matching = faker.task().get_list_in_db(service=s, current_status_type=TaskStatusType.get_done(), requestor=loggedin_user, item_count=jobs)
    unmatching = faker.task().get_list_in_db(service=s, current_status_type=TaskStatusType.get_awaiting_information(), requestor=loggedin_user, item_count=100)

    assert__page_navigation(client, 'ui.my_requests', {'_external': False, 'task_status_type_id': TaskStatusType.get_done().id}, jobs, form=TaskSearchForm(), page_size=10)


@pytest.mark.parametrize(
    "jobs",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_jobs__search__service__pages(client, faker, jobs, loggedin_user):
    service1 = faker.service().get(save=True, owners=[loggedin_user])
    service2 = faker.service().get(save=True, owners=[loggedin_user])
    matching = faker.task().get_list_in_db(service=service1, requestor=loggedin_user, item_count=jobs)
    unmatching = faker.task().get_list_in_db(service=service2, requestor=loggedin_user, item_count=100)

    assert__page_navigation(client, 'ui.my_requests', {'_external': False, 'service_id': service1.id}, jobs, form=TaskSearchForm(), page_size=10)
