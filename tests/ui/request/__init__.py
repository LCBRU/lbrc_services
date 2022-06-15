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

    mock_email.assert_any_call(
        subject="{} Request {}".format(task.service.name, context),
        message="Request has been {} for {} by {}.".format(
            context,
            task.service.name,
            user.full_name,
        ),
        recipients=task.notification_email_addresses,
        html_template='ui/email/owner_email.html',
        context=context,
        task=task,
    )


def assert__task(expected, user, data=None, files=None):
    if data is None:
        data = []
    if files is None:
        files = []

    a = _get_actual_task()

    assert a.name == expected.name
    assert a.organisation_id == expected.organisation_id
    assert a.organisation_description == expected.organisation_description
    assert a.service_id == expected.service_id
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


def post_task(client, url, task, field_data=None):
    if field_data is None:
        field_data = {}

    data={
        'name': task.name,
        'organisation_id': task.organisation_id,
        'organisation_description': task.organisation_description,
        **field_data,
    }

    if task.requestor_id:
        data['requestor_id'] = task.requestor_id

    return client.post(url, data=data)
