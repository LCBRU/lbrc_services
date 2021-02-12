from lbrc_services.model import Task, TaskStatusType
from pathlib import Path


def assert__task(expected_task, user, data=None, files=None):
    if data is None:
        data = []
    if files is None:
        files = []

    actuals = Task.query.all()
    assert len(actuals) == 1
    a = actuals[0]
    assert a.name == expected_task.name
    assert a.organisation_id == expected_task.organisation_id
    assert a.organisation_description == expected_task.organisation_description
    assert a.service_id == expected_task.service_id
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
