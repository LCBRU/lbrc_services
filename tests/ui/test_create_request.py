from pathlib import Path
import pytest
from io import BytesIO
from flask import url_for
from tests import get_test_service
from lbrc_services.model import Task, TaskStatusType
from lbrc_flask.pytest.asserts import assert__form_standards, assert__html_standards, assert__error__required_field
from lbrc_flask.pytest.helpers import get_test_field, get_test_field_group, login
from lbrc_flask.forms.dynamic import FieldType


def _url(service_id):
    return url_for('ui.create_task', service_id=service_id, _external=True)


def _assert_task(name, service, user, data=None, files=None):
    if data is None:
        data = []
    if files is None:
        files = []

    actuals = Task.query.all()
    assert len(actuals) == 1
    a = actuals[0]
    assert a.name == name
    assert a.service == service
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


    assert len(a.data) == len(data)
    for da, de in zip(a.data, data):
        assert da.task == a
        assert da.field == de['field']
        assert da.value == de['value']


def test__get__requires_login(client, faker):
    s = get_test_service(faker)
    resp = client.get(_url(service_id=s.id))
    assert resp.status_code == 302


def test__post__requires_login(client, faker):
    s = get_test_service(faker)
    resp = client.post(_url(service_id=s.id))
    assert resp.status_code == 302


def test__get__missing(client, faker):
    user = login(client, faker)

    resp = client.get(_url(service_id=999))
    assert resp.status_code == 404


def test__post__missing(client, faker):
    user = login(client, faker)

    resp = client.post(_url(service_id=999))
    assert resp.status_code == 404


@pytest.mark.app_crsf(True)
def test__standards(client, faker):
    s = get_test_service(faker)
    assert__html_standards(client, faker, _url(service_id=s.id))
    assert__form_standards(client, faker, _url(service_id=s.id))


def test__create_task__name(client, faker):
    user = login(client, faker)

    fg = get_test_field_group(faker)
    s = get_test_service(faker, field_group=fg)

    expected = faker.pystr(min_chars=5, max_chars=10)

    resp = client.post(
        _url(service_id=s.id),
        data={
            "name": expected,
        },
    )

    assert resp.status_code == 302
    _assert_task(expected, s, user)


def test__create_task__empty_name(client, faker):
    user = login(client, faker)

    fg = get_test_field_group(faker)
    s = get_test_service(faker, field_group=fg)

    resp = client.post(
        _url(service_id=s.id),
        data={
            "name": '',
        },
    )

    assert resp.status_code == 200
    assert__error__required_field(resp.soup, "name")


@pytest.mark.parametrize(
    "field_type, value, expected", [
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
def test__create_task__fields(client, faker, field_type, value, expected):
    user = login(client, faker)

    fg = get_test_field_group(faker)
    s = get_test_service(faker, field_group=fg)
    f = get_test_field(faker, field_group=fg, field_type=FieldType._get_field_type(field_type))

    expected_name = faker.pystr(min_chars=5, max_chars=10)

    field_data = {}

    if value is not None:
        field_data[f.field_name] = value

    resp = client.post(
        _url(service_id=s.id),
        data={
            "name": expected_name,
            **field_data,
        },
    )

    assert resp.status_code == 302
    _assert_task(expected_name, s, user, data=[
        {
            'field': f,
            'value': expected,
        },
    ])


@pytest.mark.parametrize(
    "choices, value, expected", [
        ('Hello|Yes', None, None),
        ('Hello|Yes', 'Hello', 'Hello'),
    ],
)
def test__create_task__fields(client, faker, choices, value, expected):
    user = login(client, faker)

    fg = get_test_field_group(faker)
    s = get_test_service(faker, field_group=fg)
    f = get_test_field(faker, field_group=fg, field_type=FieldType.get_radio(), choices=choices)

    expected_name = faker.pystr(min_chars=5, max_chars=10)

    field_data = {}

    if value is not None:
        field_data[f.field_name] = value

    resp = client.post(
        _url(service_id=s.id),
        data={
            "name": expected_name,
            **field_data,
        },
    )

    assert resp.status_code == 302
    _assert_task(expected_name, s, user, data=[
        {
            'field': f,
            'value': expected,
        },
    ])


def test__upload__upload_FileField__no_file(client, faker):
    user = login(client, faker)

    fg = get_test_field_group(faker)
    s = get_test_service(faker, field_group=fg)
    f = get_test_field(faker, field_group=fg, field_type=FieldType.get_file())

    expected_name = faker.pystr(min_chars=5, max_chars=10)

    resp = client.post(
        _url(service_id=s.id),
        data={
            "name": expected_name,
        },
    )

    assert resp.status_code == 302
    _assert_task(expected_name, s, user)


def test__upload__upload_FileField(client, faker):
    user = login(client, faker)

    fg = get_test_field_group(faker)
    s = get_test_service(faker, field_group=fg)
    f = get_test_field(faker, field_group=fg, field_type=FieldType.get_file())

    expected_name = faker.pystr(min_chars=5, max_chars=10)

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
        }
    ]

    resp = client.post(
        _url(service_id=s.id),
        data={
            "name": expected_name,
            **field_data,
        },
    )

    assert resp.status_code == 302
    _assert_task(expected_name, s, user, files=files)

    actuals = Task.query.all()
    file = actuals[0].files[0]

    assert Path(file.local_filepath).is_file()

    with open(file.local_filepath, 'r') as f:
        assert f.read() == content


def test__upload__upload_MultiFileField__no_file(client, faker):
    user = login(client, faker)

    fg = get_test_field_group(faker)
    s = get_test_service(faker, field_group=fg)
    f = get_test_field(faker, field_group=fg, field_type=FieldType.get_multifile())

    expected_name = faker.pystr(min_chars=5, max_chars=10)

    resp = client.post(
        _url(service_id=s.id),
        data={
            "name": expected_name,
        },
    )

    assert resp.status_code == 302
    _assert_task(expected_name, s, user)


@pytest.mark.parametrize(
    "n", [
        1,
        2,
        10,
    ],
)
def test__upload__upload_MultiFileField(client, faker, n):
    user = login(client, faker)

    fg = get_test_field_group(faker)
    s = get_test_service(faker, field_group=fg)
    f = get_test_field(faker, field_group=fg, field_type=FieldType.get_multifile())

    expected_name = faker.pystr(min_chars=5, max_chars=10)

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

    resp = client.post(
        _url(service_id=s.id),
        data={
            "name": expected_name,
            **field_data,
        },
    )

    assert resp.status_code == 302
    _assert_task(expected_name, s, user, files=files)

    actuals = Task.query.all()

    for fa, fe in zip(actuals[0].files, files):
        assert Path(fa.local_filepath).is_file()

        with open(fa.local_filepath, 'r') as f:
            assert f.read() == fe['content']
