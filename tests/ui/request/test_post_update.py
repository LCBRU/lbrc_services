import pytest
import http
from flask import url_for
from lbrc_services.model.services import Organisation
from lbrc_flask.pytest.asserts import assert__error__required_field_modal, assert__refresh_response, assert__requires_login
from lbrc_flask.forms.dynamic import FieldType
from tests.ui.request import assert__task, post_task


def _url(task_id, external=True):
    return url_for('ui.edit_task_modal', task_id=task_id, _external=external)


def _edit_task_post(client, task, field_data=None):
    return post_task(client, _url(task_id=task.id), task, field_data)


def test__post__requires_login(client, faker):
    task = faker.task().get_in_db()

    assert__requires_login(client, _url(task_id=task.id, external=False), post=True)


def test__post__missing(client, faker, loggedin_user):
    resp = client.post(_url(task_id=999))
    assert resp.status_code == http.HTTPStatus.NOT_FOUND


def test__update_task__with_all_values(client, faker, loggedin_user):
    task = faker.task().get_in_db(requestor=loggedin_user)

    resp = _edit_task_post(client, task)

    assert__refresh_response(resp)
    assert__task(task, loggedin_user)


def test__update_task__empty_name(client, faker, loggedin_user):
    task = faker.task().get_in_db(requestor=loggedin_user)
    task.name = ''

    resp = _edit_task_post(client, task)

    assert resp.status_code == http.HTTPStatus.OK
    assert__error__required_field_modal(resp.soup, "request title")


def test__update_task__empty_organisation(client, faker, loggedin_user):
    task = faker.task().get_in_db(requestor=loggedin_user)
    task.organisations = []

    resp = _edit_task_post(client, task)

    assert resp.status_code == http.HTTPStatus.OK
    assert__error__required_field_modal(resp.soup, "organisations")


@pytest.mark.parametrize(
    "field_type, original_value, value, expected_value", [
        (FieldType.BOOLEAN, '1', None, '0'),
        (FieldType.BOOLEAN, '0', True, '1'),
        (FieldType.INTEGER, '55', None, '55'),
        (FieldType.INTEGER, '99', 1, '1'),
        (FieldType.INTEGER, '99', 678, '678'),
        (FieldType.STRING, 'Blurb', None, 'Blurb'),
        (FieldType.STRING, 'Tennis', '', ''),
        (FieldType.STRING, 'Cod', 'Makes a tackle for a loss!', 'Makes a tackle for a loss!'),
        (FieldType.TEXTAREA, 'Frederick', None, 'Frederick'),
        (FieldType.TEXTAREA, 'Haste', '', ''),
        (FieldType.TEXTAREA, 'Tom Brady', 'This is the Mahomes magic', 'This is the Mahomes magic'),
    ],
)
def test__update_task__fields(client, faker, field_type, original_value, value, expected_value, loggedin_user):
    s, f = faker.get_test_field_of_type(FieldType._get_field_type(field_type))

    field_data = {}
    data = []

    if value is not None:
        field_data[f.field_name] = value

    data.append({
        'field': f,
        'value': expected_value,
    })

    task = faker.task().get_in_db(service=s, requestor=loggedin_user)
    orig = faker.task_data().get_in_db(task=task, field=f, value=original_value)

    resp = _edit_task_post(client, task, field_data)

    assert__refresh_response(resp)
    assert__task(task, loggedin_user, data=data)


@pytest.mark.parametrize(
    "choices, original_value, value, expected_value", [
        ('Hello|Yes', '', None, ''),
        ('Hello|Yes', 'Yes', '', 'Yes'),
        ('Hello|Yes', 'Yes', 'Hello', 'Hello'),
    ],
)
def test__update_task__radio_fields(client, faker, choices, original_value, value, expected_value, loggedin_user):
    s, f = faker.get_test_field_of_type(FieldType.get_radio(), choices=choices)

    field_data = {}
    data = []

    if value:
        field_data[f.field_name] = value

    data.append({
        'field': f,
        'value': expected_value,
    })

    task = faker.task().get_in_db(service=s, requestor=loggedin_user)
    orig = faker.task_data().get_in_db(task=task, field=f, value=original_value)

    resp = _edit_task_post(client, task, field_data)

    assert__refresh_response(resp)
    assert__task(task, loggedin_user, data=data)


def test__update_task__upload_FileField__no_file(client, faker, loggedin_user):
    s, f = faker.get_test_field_of_type(FieldType.get_file())

    files=[]

    task = faker.task().get_in_db(service=s, requestor=loggedin_user)

    orig1 = faker.fake_file()
    faker.create_task_file_in_filesystem(
        task_file=faker.task_file().get_in_db(task=task, field=f, filename=orig1.filename),
        fake_file=orig1,
    )
    files.append({'field': f, 'file': orig1})

    resp = _edit_task_post(client, task)

    assert__refresh_response(resp)
    assert__task(task, loggedin_user, files=files)


def test__update_task__upload_FileField(client, faker, loggedin_user):
    s, f = faker.get_test_field_of_type(FieldType.get_file())

    field_data = {}
    files = []

    fake_file = faker.fake_file()

    field_data[f.field_name] = fake_file.file_tuple()

    task = faker.task().get_in_db(service=s, requestor=loggedin_user)

    orig1 = faker.fake_file()
    faker.create_task_file_in_filesystem(
        task_file=faker.task_file().get_in_db(task=task, field=f, filename=orig1.filename),
        fake_file=orig1,
    )
    files.append({'field': f, 'file': orig1})

    files.append({
        'field': f,
        'file': fake_file,
    })

    resp = _edit_task_post(client, task, field_data)

    assert__refresh_response(resp)
    assert__task(task, loggedin_user, files=files)


def test__update_task__upload_MultiFileField__no_file(client, faker, loggedin_user):
    s, f = faker.get_test_field_of_type(FieldType.get_multifile())

    files = []

    task = faker.task().get_in_db(service=s, requestor=loggedin_user)

    orig1 = faker.fake_file()
    faker.create_task_file_in_filesystem(
        task_file=faker.task_file().get_in_db(task=task, field=f, filename=orig1.filename),
        fake_file=orig1,
    )
    files.append({'field': f, 'file': orig1})

    orig2 = faker.fake_file()
    faker.create_task_file_in_filesystem(
        task_file=faker.task_file().get_in_db(task=task, field=f, filename=orig2.filename),
        fake_file=orig2,
    )
    files.append({'field': f, 'file': orig2})

    resp = _edit_task_post(client, task)

    assert__refresh_response(resp)
    assert__task(task, loggedin_user, files=files)


@pytest.mark.parametrize(
    "n", [
        1,
        2,
        10,
    ],
)
def test__update_task__upload_MultiFileField(client, faker, n, loggedin_user):
    s, f = faker.get_test_field_of_type(FieldType.get_multifile())

    field_data = {
        f.field_name: [],
    }
    files = []

    task = faker.task().get_in_db(service=s, requestor=loggedin_user)

    orig1 = faker.fake_file()
    faker.create_task_file_in_filesystem(
        task_file=faker.task_file().get_in_db(task=task, field=f, filename=orig1.filename),
        fake_file=orig1,
    )
    files.append({'field': f, 'file': orig1})

    orig2 = faker.fake_file()
    faker.create_task_file_in_filesystem(
        task_file=faker.task_file().get_in_db(task=task, field=f, filename=orig2.filename),
        fake_file=orig2,
    )
    files.append({'field': f, 'file': orig2})

    for _ in range(n):
        fake_file = faker.fake_file()

        field_data[f.field_name].append(fake_file.file_tuple())

        files.append({
            'field': f,
            'file': fake_file,
        })

    resp = _edit_task_post(client, task, field_data)

    assert__refresh_response(resp)
    assert__task(task, loggedin_user, files=files)
