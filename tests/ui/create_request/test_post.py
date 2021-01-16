from pathlib import Path
from flask_api import status
from tests.ui.create_request import _url
import pytest
from io import BytesIO
from tests import get_test_service
from lbrc_services.model import Organisation, Task, TaskStatusType
from lbrc_flask.pytest.asserts import assert__error__required_field, assert__redirect, assert__requires_login
from lbrc_flask.pytest.helpers import get_test_field, get_test_field_group, login
from lbrc_flask.forms.dynamic import FieldType


def get_test_field_of_type(faker, field_type, choices=None):
    fg = get_test_field_group(faker)
    s = get_test_service(faker, field_group=fg)
    f = get_test_field(faker, field_group=fg, field_type=field_type, choices=choices)
    return s,f


def _create_task_post(client, task, field_data=None):
    if field_data is None:
        field_data = {}

    return client.post(
        _url(service_id=task.service_id),
        data={
            'name': task.name,
            'organisation_id': task.organisation_id,
            **field_data,
        },
    )


def _assert_task(expected_task, user, data=None, files=None):
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
    assert s.notes == ''
    assert s.task_status_type == TaskStatusType.get_created()

    assert len(a.files) == len(files)
    for da, de in zip(a.files, files):
        assert da.task == a
        assert da.field == de['field']
        assert da.filename == de['filename']
        assert len(da.local_filepath) > 0

        assert Path(da.local_filepath).is_file()

        with open(da.local_filepath, 'r') as f:
            assert f.read() == de['content']

    assert len(a.data) == len(data)
    for da, de in zip(a.data, data):
        assert da.task == a
        assert da.field == de['field']
        assert da.value == de['value']


def test__post__requires_login(client, faker):
    s = get_test_service(faker)
    assert__requires_login(client, 'ui.create_task', post=True, service_id=s.id)


def test__post__missing(client, faker):
    user = login(client, faker)

    resp = client.post(_url(service_id=999))
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test__create_task__with_all_values(client, faker):
    user = login(client, faker)

    expected = faker.task_details(service=get_test_service(faker))

    resp = _create_task_post(client, expected)

    assert__redirect(resp, endpoint='ui.index')
    _assert_task(expected, user)


def test__create_task__empty_name(client, faker):
    user = login(client, faker)

    expected = faker.task_details(service=get_test_service(faker), name='')

    resp = _create_task_post(client, expected)

    assert resp.status_code == status.HTTP_200_OK
    assert__error__required_field(resp.soup, "name")


def test__create_task__empty_organisation(client, faker):
    user = login(client, faker)

    expected = faker.task_details(service=get_test_service(faker))
    expected.organisation_id = None

    resp = _create_task_post(client, expected)

    assert resp.status_code == status.HTTP_200_OK
    assert__error__required_field(resp.soup, "organisation")


def test__create_task__empty_requestor__uses_current_user(client, faker):
    user = login(client, faker)

    expected = faker.task_details(service=get_test_service(faker))
    expected.requestor_id = None

    resp = _create_task_post(client, expected)

    assert__redirect(resp, endpoint='ui.index')
    expected.requestor_id = user.id
    _assert_task(expected, user)


def test__create_task__empty_organisation_description__when_organisation_is_other(client, faker):
    user = login(client, faker)

    expected = faker.task_details(service=get_test_service(faker), organisation=Organisation.get_other())

    resp = _create_task_post(client, expected)

    assert resp.status_code == status.HTTP_200_OK
    print(resp.soup)
    assert__error__required_field(resp.soup, "organisation description")


@pytest.mark.parametrize(
    "field_type, value, expected_value", [
        (FieldType.BOOLEAN, None, '0'),
        (FieldType.BOOLEAN, True, '1'),
        (FieldType.INTEGER, None, None),
        (FieldType.INTEGER, 1, '1'),
        (FieldType.INTEGER, 678, '678'),
        (FieldType.STRING, None, ''),
        (FieldType.STRING, '', ''),
        (FieldType.STRING, 'Makes a tackle for a loss!', 'Makes a tackle for a loss!'),
        (FieldType.TEXTAREA, None, ''),
        (FieldType.TEXTAREA, '', ''),
        (FieldType.TEXTAREA, 'This is the Mahomes magic', 'This is the Mahomes magic'),
    ],
)
def test__create_task__fields(client, faker, field_type, value, expected_value):
    user = login(client, faker)

    s, f = get_test_field_of_type(faker, FieldType._get_field_type(field_type))

    field_data = {}

    if value is not None:
        field_data[f.field_name] = value

    expected = faker.task_details(service=s)

    resp = _create_task_post(client, expected, field_data)

    assert__redirect(resp, endpoint='ui.index')
    _assert_task(expected, user, data=[
        {
            'field': f,
            'value': expected_value,
        },
    ])


@pytest.mark.parametrize(
    "choices, value, expected_value", [
        ('Hello|Yes', None, None),
        ('Hello|Yes', 'Hello', 'Hello'),
    ],
)
def test__create_task__radio_fields(client, faker, choices, value, expected_value):
    user = login(client, faker)

    s, f = get_test_field_of_type(faker, FieldType.get_radio(), choices=choices)

    field_data = {}

    if value is not None:
        field_data[f.field_name] = value

    expected = faker.task_details(service=s)

    resp = _create_task_post(client, expected, field_data)

    assert__redirect(resp, endpoint='ui.index')
    _assert_task(expected, user, data=[
        {
            'field': f,
            'value': expected_value,
        },
    ])


def test__upload__upload_FileField__no_file(client, faker):
    user = login(client, faker)

    s, f = get_test_field_of_type(faker, FieldType.get_file())

    expected = faker.task_details(service=s)
    resp = _create_task_post(client, expected)

    assert__redirect(resp, endpoint='ui.index')
    _assert_task(expected, user)


def test__upload__upload_FileField(client, faker):
    user = login(client, faker)

    s, f = get_test_field_of_type(faker, FieldType.get_file())

    field_data = {}

    content = faker.text()
    filename = faker.file_name(extension='pdf')

    field_data[f.field_name] = (
        BytesIO(content.encode('utf-8')),
        filename
    )

    files = [
        {
            'field': f,
            'filename': filename,
            'content': content,
        }
    ]

    expected = faker.task_details(service=s)
    resp = _create_task_post(client, expected, field_data)

    assert__redirect(resp, endpoint='ui.index')
    _assert_task(expected, user, files=files)


def test__upload__upload_MultiFileField__no_file(client, faker):
    user = login(client, faker)

    s, f = get_test_field_of_type(faker, FieldType.get_multifile())

    expected = faker.task_details(service=s)
    resp = _create_task_post(client, expected)

    assert__redirect(resp, endpoint='ui.index')
    _assert_task(expected, user)


@pytest.mark.parametrize(
    "n", [
        1,
        2,
        10,
    ],
)
def test__upload__upload_MultiFileField(client, faker, n):
    user = login(client, faker)

    s, f = get_test_field_of_type(faker, FieldType.get_multifile())

    field_data = {
        f.field_name: [],
    }
    files = []

    for _ in range(n):
        content = faker.text()
        filename = faker.file_name(extension='pdf')

        field_data[f.field_name].append((
            BytesIO(content.encode('utf-8')),
            filename
        ))

        files.append({
            'field': f,
            'filename': filename,
            'content': content,
        })

    expected = faker.task_details(service=s)
    resp = _create_task_post(client, expected, field_data)

    assert__redirect(resp, endpoint='ui.index')
    _assert_task(expected, user, files=files)
