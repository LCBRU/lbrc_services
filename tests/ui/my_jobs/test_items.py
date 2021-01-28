import pytest
import re
from flask import url_for
from lbrc_services.model import TaskStatusType
from tests import lbrc_services_get, get_test_owned_task, get_test_user
from lbrc_flask.pytest.asserts import assert__requires_login, assert__search_html
from flask_api import status
from lbrc_services.ui.forms import _get_combined_task_status_type_choices, _get_service_choices, _get_requestor_choices
from lbrc_flask.pytest.asserts import assert__select

def _url(external=True, **kwargs):
    return url_for('ui.my_jobs', _external=external, **kwargs)


def _get(client, url, loggedin_user, has_form):
    resp = lbrc_services_get(client, url, loggedin_user, has_form)

    assert__search_html(resp.soup, clear_url=_url(external=False))

    assert__select(soup=resp.soup, id='service_id', options=_get_service_choices())
    assert__select(soup=resp.soup, id='task_status_type_id', options=_get_combined_task_status_type_choices())
    assert__select(soup=resp.soup, id='requestor_id', options=_get_requestor_choices())

    return resp


def test__get__requires_login(client):
    assert__requires_login(client, _url(external=False))


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    ["mine", "others"],
    [(0, 0), (0, 1), (0, 0), (2, 2), (3, 0)],
)
def test__my_jobs(client, faker, mine, others, loggedin_user):
    user2 = get_test_user(faker)

    my_jobs = [get_test_owned_task(faker, owner=loggedin_user) for _ in range(mine)]
    others_jobs = [get_test_owned_task(faker, owner=user2) for _ in range(others)]

    resp = _get(client, _url(), loggedin_user, has_form=True)

    assert_results(resp, my_jobs)


@pytest.mark.app_crsf(True)
def test__my_jobs__search__name(client, faker, loggedin_user):
    matching = get_test_owned_task(faker, name='Mary', owner=loggedin_user)
    non_matching = get_test_owned_task(faker, name='Joseph', owner=loggedin_user)

    resp = _get(client, _url(search='ar'), loggedin_user, has_form=True)

    assert_results(resp, [matching])


@pytest.mark.app_crsf(True)
def test__my_jobs__search__task_status_type(client, faker, loggedin_user):
    s = faker.service_details(owners=[loggedin_user])

    matching = get_test_owned_task(faker, current_status_type=TaskStatusType.get_done(), owner=loggedin_user)
    non_matching = get_test_owned_task(faker, current_status_type=TaskStatusType.get_awaiting_information(), owner=loggedin_user)

    resp = _get(client, _url(task_status_type_id=TaskStatusType.get_done().id), loggedin_user, has_form=True)

    assert_results(resp, [matching])


@pytest.mark.app_crsf(True)
def test__my_jobs__search__service(client, faker, loggedin_user):
    matching = get_test_owned_task(faker, owner=loggedin_user)
    non_matching = get_test_owned_task(faker, owner=loggedin_user)

    resp = _get(client, _url(service_id=matching.service.id), loggedin_user, has_form=True)

    assert_results(resp, [matching])


@pytest.mark.app_crsf(True)
def test__my_jobs__search__requestor(client, faker, loggedin_user):
    matching = get_test_owned_task(faker, owner=loggedin_user)
    non_matching = get_test_owned_task(faker, owner=loggedin_user)

    resp = _get(client, _url(requestor_id=matching.requestor.id), loggedin_user, has_form=True)

    assert_results(resp, [matching])


def assert_results(resp, matches):
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.soup.find_all("li", "list-group-item")) == len(matches)

    for u, li in zip(matches, resp.soup.find_all("li", "list-group-item")):
        task_matches_li(u, li)


def task_matches_li(task, li):
    assert li.find("h1").find(string=re.compile(task.service.name)) is not None
    assert li.find("h1").find(string=re.compile(task.name)) is not None
    assert li.find("h2").find(string=re.compile(task.requestor.full_name)) is not None

    assert len(li.select('a[href*="{}"]'.format(url_for('ui.edit_task', task_id=task.id, prev=_url(external=False))))) == 1
    assert len(li.select('a[href*="{}"]'.format(url_for('ui.task_todo_list', task_id=task.id, prev=_url(external=False))))) == 1

    assert li.find("button", "btn").find(string=re.compile(task.current_status_type.name)) is not None
    assert li.find("div", "dropdown-menu").find('a', string='Update Status') is not None
    assert li.find("div", "dropdown-menu").find('a', string='Show History') is not None
