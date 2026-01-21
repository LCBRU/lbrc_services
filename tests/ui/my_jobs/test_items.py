import pytest
import re
import http
from flask import url_for
from lbrc_services.model.services import TaskStatusType
from tests import lbrc_services_get
from lbrc_flask.pytest.asserts import assert__requires_login, assert__search_html
from lbrc_services.ui.forms import MyJobsSearchForm, _get_combined_task_status_type_choices, _get_service_choices, _get_requestor_choices
from lbrc_flask.pytest.asserts import assert__select, assert__page_navigation


def _url(external=True, **kwargs):
    return url_for('ui.my_jobs', _external=external, **kwargs)


def _get(client, url, loggedin_user, has_form):
    resp = lbrc_services_get(client, url, loggedin_user, has_form)

    assert__search_html(resp.soup)

    assert__select(soup=resp.soup, id='service_id', options=dict(_get_service_choices()))
    assert__select(soup=resp.soup, id='task_status_type_id', options=dict(_get_combined_task_status_type_choices()))
    assert__select(soup=resp.soup, id='requestor_id', options=dict(_get_requestor_choices()))

    return resp


def test__get__requires_login(client):
    assert__requires_login(client, _url(external=False))


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    ["mine", "others"],
    [(0, 0), (0, 1), (0, 0), (2, 2), (3, 0)],
)
def test__my_jobs(client, faker, mine, others, loggedin_user):
    user2 = faker.user().get(save=True)

    my_service = faker.service().get(save=True, owners=[loggedin_user])
    other_service = faker.service().get(save=True, owners=[user2])
    my_jobs = faker.task().get_list(save=True, service=my_service, owner=loggedin_user, item_count=mine)
    others_jobs = faker.task().get_list(save=True, service=other_service, owner=user2, item_count=others)

    resp = _get(client, _url(), loggedin_user, has_form=False)

    assert_results(resp, my_jobs)


@pytest.mark.app_crsf(True)
def test__my_jobs__search__name(client, faker, loggedin_user):
    s = faker.service().get(save=True, owners=[loggedin_user])
    matching = faker.task().get(save=True, service=s, name='Mary', owner=loggedin_user)
    non_matching = faker.task().get(save=True, service=s, name='Joseph', owner=loggedin_user)

    resp = _get(client, _url(search='ar'), loggedin_user, has_form=False)

    assert_results(resp, [matching])


@pytest.mark.app_crsf(True)
def test__my_jobs__search__task_status_type(client, faker, loggedin_user):
    s = faker.service().get(save=True, owners=[loggedin_user])
    matching = faker.task().get(save=True, service=s, current_status_type=TaskStatusType.get_done(), owner=loggedin_user)
    non_matching = faker.task().get(save=True, service=s, current_status_type=TaskStatusType.get_awaiting_information(), owner=loggedin_user)

    resp = _get(client, _url(task_status_type_id=TaskStatusType.get_done().id), loggedin_user, has_form=False)

    assert_results(resp, [matching])


@pytest.mark.app_crsf(True)
def test__my_jobs__search__service(client, faker, loggedin_user):
    matching_service = faker.service().get(save=True, owners=[loggedin_user])
    non_matching_service = faker.service().get(save=True, owners=[loggedin_user])
    matching = faker.task().get(save=True, service=matching_service, owner=loggedin_user)
    non_matching = faker.task().get(save=True, service=non_matching_service, owner=loggedin_user)

    resp = _get(client, _url(service_id=matching.service.id), loggedin_user, has_form=False)

    assert_results(resp, [matching])


@pytest.mark.app_crsf(True)
def test__my_jobs__search__requestor(client, faker, loggedin_user):
    s = faker.service().get(save=True, owners=[loggedin_user])
    matching = faker.task().get(save=True, service=s, owner=loggedin_user)
    non_matching = faker.task().get(save=True, service=s, owner=loggedin_user)

    resp = _get(client, _url(requestor_id=matching.requestor.id), loggedin_user, has_form=False)

    assert_results(resp, [matching])


def assert_results(resp, matches):
    assert resp.status_code == http.HTTPStatus.OK
    assert len(resp.soup.select(".panel_list > li")) == len(matches)

    for u, li in zip(matches, resp.soup.find_all(".panel_list > li")):
        task_matches_li(u, li)


def task_matches_li(task, li):
    assert li.find("h1").find(string=re.compile(task.service.name)) is not None
    assert li.find("h1").find(string=re.compile(task.name)) is not None
    assert li.find("h2").find(string=re.compile(task.requestor.full_name)) is not None

    assert len(li.select('a[href*="{}"]'.format(url_for('ui.edit_task', task_id=task.id, prev=_url(external=False))))) == 1
    assert len(li.select('a[href*="{}"]'.format(url_for('ui.task_todo_list', task_id=task.id, prev=_url(external=False))))) == 1

    assert li.find("button", "btn", string=re.compile('{}'.format(task.current_status_type.name))) is not None

    assert li.find('a', string='Update Status') is not None
    assert li.find('a', string='Show History') is not None


@pytest.mark.parametrize(
    "jobs",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_jobs__pages(client, faker, jobs, loggedin_user):
    s = faker.service().get(save=True, owners=[loggedin_user])
    my_jobs = faker.task().get_list(save=True, service=s, owner=loggedin_user, requestor=loggedin_user, item_count=jobs)

    assert__page_navigation(client, 'ui.my_jobs', {'_external': False}, jobs, form=MyJobsSearchForm(), page_size=10)


@pytest.mark.parametrize(
    "jobs",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_jobs__search__name__pages(client, faker, jobs, loggedin_user):
    s = faker.service().get(save=True, owners=[loggedin_user])
    matching = faker.task().get_list(save=True, service=s, name='Mary', owner=loggedin_user, requestor=loggedin_user, item_count=jobs)
    unmatching = faker.task().get_list(save=True, service=s, name='Joseph', owner=loggedin_user, requestor=loggedin_user, item_count=100)

    assert__page_navigation(client, 'ui.my_jobs', {'_external': False, 'search': 'ar'}, jobs, form=MyJobsSearchForm(), page_size=10)


@pytest.mark.parametrize(
    "jobs",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_jobs__search__task_status__pages(client, faker, jobs, loggedin_user):
    s = faker.service().get(save=True, owners=[loggedin_user])
    matching = faker.task().get_list(save=True, service=s, current_status_type=TaskStatusType.get_done(), owner=loggedin_user, requestor=loggedin_user, item_count=jobs)
    unmatching = faker.task().get_list(save=True, service=s, current_status_type=TaskStatusType.get_awaiting_information(), owner=loggedin_user, requestor=loggedin_user, item_count=100)

    assert__page_navigation(client, 'ui.my_jobs', {'_external': False, 'task_status_type_id': TaskStatusType.get_done().id}, jobs, form=MyJobsSearchForm(), page_size=10)


@pytest.mark.parametrize(
    "jobs",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__my_jobs__search__service__pages(client, faker, jobs, loggedin_user):
    service1 = faker.service().get(save=True, owners=[loggedin_user])
    service2 = faker.service().get(save=True, owners=[loggedin_user])
    matching = faker.task().get_list(save=True, service=service1, requestor=loggedin_user, item_count=jobs)
    unmatching = faker.task().get_list(save=True, service=service2, requestor=loggedin_user, item_count=100)

    assert__page_navigation(client, 'ui.my_jobs', {'_external': False, 'service_id': service1.id}, jobs, form=MyJobsSearchForm(), page_size=10)
