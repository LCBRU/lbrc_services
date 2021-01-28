from lbrc_services.model import ToDo
from tests import get, get_test_task, get_test_todo
import pytest
from flask import url_for
from lbrc_flask.pytest.asserts import assert__requires_login


def _url(external=True, **kwargs):
    return url_for('ui.task_todo_list', _external=external, **kwargs)


def test__get__requires_login(client, faker):
    t = get_test_task(faker)
    assert__requires_login(client, _url(task_id=t.id, external=False))


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    ["for_this_task", "for_other_tasks"],
    [(0, 0), (0, 1), (0, 0), (2, 2), (3, 0)],
)
def test__todos(client, faker, for_this_task, for_other_tasks, loggedin_user):
    this_task = get_test_task(faker)
    other_task = get_test_task(faker)

    this_task_todos = [get_test_todo(faker, task=this_task) for _ in range(for_this_task)]
    other_task_todos = [get_test_todo(faker, task=other_task) for _ in range(for_other_tasks)]

    resp = get(client, _url(task_id=this_task.id), loggedin_user, has_form=True)

    assert_results(resp, this_task_todos)


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    ["status_code", "status_name"], ToDo._status_map.items(),
)
def test__todo__statuses(client, faker, status_code, status_name, loggedin_user):
    todo = get_test_todo(faker, status=status_code)

    resp = get(client, _url(task_id=todo.task.id), loggedin_user, has_form=True)

    assert_results(resp, [todo])


@pytest.mark.app_crsf(True)
def test__todo__search__name(client, faker, loggedin_user):
    task = get_test_task(faker)

    matching = get_test_todo(faker, task=task, description="Mary")
    un_matching = get_test_todo(faker, task=task, description="Joseph")

    resp = get(client, _url(task_id=task.id, search='ar'), loggedin_user, has_form=True)

    assert_results(resp, [matching])


def assert_results(resp, matches):
    assert resp.status_code == 200
    assert len(resp.soup.find_all("li", "list-group-item")) == len(matches)

    for u, li in zip(matches, resp.soup.find_all("li", "list-group-item")):
        task_matches_li(u, li)


def task_matches_li(todo, li):

    assert li.find("p", string=todo.description) is not None
    assert li.find("a", "todo_edit") is not None

    todo_checkbox = li.find("a", "todo_checkbox")
    assert todo_checkbox is not None

    if todo.status == ToDo.OUTSTANDING:
        assert todo_checkbox['data-action'] == 'check'
    elif todo.status == ToDo.COMPLETED:
        assert todo_checkbox['data-action'] == 'unneeded'
    elif todo.status == ToDo.NOT_REQUIRED:
        assert todo_checkbox['data-action'] == 'uncheck'
