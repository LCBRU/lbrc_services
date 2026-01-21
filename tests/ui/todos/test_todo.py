from lbrc_services.model.services import ToDo
from tests import lbrc_services_modal_get
import pytest
from flask import url_for
from lbrc_flask.pytest.asserts import assert__requires_login


def _url(external=True, **kwargs):
    return url_for('ui.task_todos', _external=external, **kwargs)


# @pytest.mark.skip(reason="Flask_Login is adding extra parameters to URL")
def test__get__requires_login(client, faker):
    t = faker.task().get(save=True)
    assert__requires_login(client, _url(task_id=t.id, external=False))


@pytest.mark.parametrize(
    ["for_this_task", "for_other_tasks"],
    [(0, 0), (0, 1), (0, 0), (2, 2), (3, 0)],
)
def test__todos(client, faker, for_this_task, for_other_tasks, loggedin_user):
    s = faker.service().get(save=True, owners=[loggedin_user])
    this_task = faker.task().get(save=True, service=s)
    other_task = faker.task().get(save=True)

    this_task_todos = [faker.todo().get(save=True, task=this_task) for _ in range(for_this_task)]
    other_task_todos = [faker.todo().get(save=True, task=other_task) for _ in range(for_other_tasks)]

    resp = lbrc_services_modal_get(client, _url(task_id=this_task.id), has_form=False)
