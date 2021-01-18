from lbrc_services.model import ToDo
from tests import get_test_task
import pytest
from flask import url_for
from lbrc_flask.database import db
from lbrc_flask.pytest.helpers import login
from lbrc_flask.pytest.asserts import assert__form_standards, assert__html_standards, assert__requires_login


def _url(external=True, **kwargs):
    return url_for('ui.task_todo_list', _external=external, **kwargs)


def test__get__requires_login(client, faker):
    t = get_test_task(faker)
    assert__requires_login(client, _url(task_id=t.id, external=False))


@pytest.mark.app_crsf(True)
def test__standards(client, faker):
    t = get_test_task(faker)
    assert__html_standards(client, faker, _url(task_id=t.id))
    assert__form_standards(client, faker, _url(task_id=t.id))


@pytest.mark.parametrize(
    ["for_this_task", "for_other_tasks"],
    [(0, 0), (0, 1), (0, 0), (2, 2), (3, 0)],
)
def test__todos(client, faker, for_this_task, for_other_tasks):
    user = login(client, faker)

    this_task = get_test_task(faker)
    other_task = get_test_task(faker)

    this_task_todos = [faker.todo_details(task=this_task) for _ in range(for_this_task)]
    db.session.add_all(this_task_todos)
    db.session.add_all([faker.todo_details(task=other_task) for _ in range(for_other_tasks)])
    db.session.commit()

    resp = client.get(_url(task_id=this_task.id))

    assert_results(resp, this_task_todos)


@pytest.mark.parametrize(
    ["status_code", "status_name"], ToDo._status_map.items(),
)
def test__todo__statuses(client, faker, status_code, status_name):
    user = login(client, faker)

    task = get_test_task(faker)

    todo = faker.todo_details(task=task, status=status_code)

    db.session.add(todo)
    db.session.commit()

    resp = client.get(_url(task_id=task.id))

    assert_results(resp, [todo])


def test__todo__search__name(client, faker):
    user = login(client, faker)

    task = get_test_task(faker)

    matching = faker.todo_details(task=task, description="Mary")
    db.session.add(matching)
    db.session.add(faker.todo_details(task=task, description='Joseph'))
    db.session.commit()

    resp = client.get(_url(task_id=task.id,search='ar'))

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
