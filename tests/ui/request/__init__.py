import pytest
from lbrc_services.model.services import Task, TaskStatusType
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(scope="function")
def mock_email():
    with patch('lbrc_services.ui.views.task.email') as mock:
        yield mock


def _get_actual_task():
    actuals = Task.query.all()
    assert len(actuals) == 1
    return actuals[0]   


def assert_emails_sent(mock_email, context, user):
    task = _get_actual_task()

    mock_email.assert_called()


def assert__task(expected, user, service, data=None, files=None, expected_organisations=None):
    data = data or []
    files = files or []
    expected_organisations = expected_organisations or []

    a = _get_actual_task()

    assert a.name == expected.name
    assert a.organisations == expected_organisations
    assert a.organisation_description == expected.organisation_description
    assert a.service_id == service.id
    assert a.requestor == user
    assert a.current_status_type == TaskStatusType.get_created()
    assert len(a.status_history) == 1
    s = a.status_history[0]
    assert s.task == a
    assert len(s.notes) > 0
    assert s.task_status_type == TaskStatusType.get_created()

    assert len(a.files) == len(files)
    for da, de in zip(a.files, files):
        assert da.task == a
        assert da.field == de['field']
        assert da.filename == de['file'].filename
        assert len(da.local_filepath) > 0

        assert Path(da.local_filepath).is_file()

        with open(da.local_filepath, 'r') as f:
            assert f.read() == de['file'].content

    assert len(a.data) == len(data)
    for da, de in zip(a.data, data):
        assert da.task == a
        assert da.field == de['field']
        assert da.value == de['value']


def post_task(client, url, task, organisations=None, field_data=None):
    field_data = field_data or {}
    organisations = organisations or []

    data={
        'name': task.name,
        'organisations': [o.id for o in organisations],
        'organisation_description': task.organisation_description,
        **field_data,
    }

    if task.requestor_id:
        data['requestor_id'] = task.requestor_id

    return client.post(url, data=data)
