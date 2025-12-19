import pytest
import http
from flask import url_for
from lbrc_services.model.services import Organisation
from lbrc_flask.pytest.asserts import assert__error__required_field_modal, assert__refresh_response, assert__requires_login
from lbrc_flask.forms.dynamic import FieldType
from tests.ui.request import assert__task, post_task, assert_emails_sent, mock_email


def _url(service_id, external=True):
    return url_for('ui.create_task', service_id=service_id, _external=external)


def _create_task_post(client, task, service, organisations=None, field_data=None):
    url = _url(service_id=service.id)
    return post_task(client, url, task, field_data=field_data, organisations=organisations)


def test__post__requires_login(client, faker):
    s = faker.service().get_in_db()
    assert__requires_login(client, _url(service_id=s.id, external=False), post=True)


def test__post__missing(client, faker, loggedin_user):
    resp = client.post(_url(service_id=999))
    assert resp.status_code == http.HTTPStatus.NOT_FOUND


def test__create_task__with_all_values(client, faker, loggedin_user, mock_email):
    service = faker.service().get_in_db()
    organisation = faker.organisation().get_in_db()
    expected = faker.task().get()

    resp = _create_task_post(client, expected, service=service, organisations=[organisation])

    assert_emails_sent(mock_email, context='created', user=loggedin_user)
    assert__refresh_response(resp)
    assert__task(expected, loggedin_user, service=service, expected_organisations=[organisation])


def test__create_task__empty_name(client, faker, loggedin_user):
    service = faker.service().get_in_db()
    organisation = faker.organisation().get_in_db()
    expected = faker.task().get(name='')

    resp = _create_task_post(client, expected, service=service, organisations=[organisation])

    assert resp.status_code == http.HTTPStatus.OK
    assert__error__required_field_modal(resp.soup, "request title")


def test__create_task__empty_organisation(client, faker, loggedin_user):
    service = faker.service().get_in_db()
    expected = faker.task().get()
    expected.organisations = []

    resp = _create_task_post(client, expected, service=service, organisations=[])

    assert resp.status_code == http.HTTPStatus.OK
    assert__error__required_field_modal(resp.soup, "organisations")


def test__create_task__empty_requestor__uses_current_user(client, faker, loggedin_user, mock_email):
    service = faker.service().get_in_db()
    organisation = faker.organisation().get_in_db()
    expected = faker.task().get()
    expected.requestor = None

    resp = _create_task_post(client, expected, service=service, organisations=[organisation])

    assert_emails_sent(mock_email, context='created', user=loggedin_user)
    assert__refresh_response(resp)
    expected.requestor_id = loggedin_user.id
    assert__task(expected, loggedin_user, service=service, expected_organisations=[organisation])


def test__create_task__empty_organisation_description__when_organisation_is_other(client, faker, loggedin_user):
    service = faker.service().get_in_db()
    organisation = Organisation.get_other()
    expected = faker.task().get()

    resp = _create_task_post(client, expected, service=service, organisations=[organisation])

    assert resp.status_code == http.HTTPStatus.OK
    assert__error__required_field_modal(resp.soup, "organisation description")


@pytest.mark.parametrize(
    "field_type, value, expected_value", [
        (FieldType.BOOLEAN, None, '0'),
        (FieldType.BOOLEAN, True, '1'),
        (FieldType.INTEGER, None, None),
        (FieldType.INTEGER, 1, '1'),
        (FieldType.INTEGER, 678, '678'),
        (FieldType.STRING, None, None),
        (FieldType.STRING, '', ''),
        (FieldType.STRING, 'Makes a tackle for a loss!', 'Makes a tackle for a loss!'),
        (FieldType.TEXTAREA, None, None),
        (FieldType.TEXTAREA, '', ''),
        (FieldType.TEXTAREA, 'This is the Mahomes magic', 'This is the Mahomes magic'),
    ],
)
def test__create_task__fields(client, faker, field_type, value, expected_value, loggedin_user, mock_email):
    s, f = faker.get_test_field_of_type(FieldType._get_field_type(field_type))

    field_data = {}

    if value is not None:
        field_data[f.field_name] = value

    organisation = faker.organisation().get_in_db()
    expected = faker.task().get()

    resp = _create_task_post(client, expected, field_data=field_data, service=s, organisations=[organisation])

    assert_emails_sent(mock_email, context='created', user=loggedin_user)
    assert__refresh_response(resp)
    assert__task(expected, loggedin_user, service=s, data=[
        {
            'field': f,
            'value': expected_value,
        },
        ],
        expected_organisations=[organisation]
    )


@pytest.mark.parametrize(
    "choices, value, expected_value", [
        ('Hello|Yes', None, None),
        ('Hello|Yes', 'Hello', 'Hello'),
    ],
)
def test__create_task__radio_fields(client, faker, choices, value, expected_value, loggedin_user, mock_email):
    s, f = faker.get_test_field_of_type(FieldType.get_radio(), choices=choices)

    field_data = {}

    if value is not None:
        field_data[f.field_name] = value

    organisation = faker.organisation().get_in_db()
    expected = faker.task().get()

    resp = _create_task_post(client, expected, field_data=field_data, service=s, organisations=[organisation])

    assert_emails_sent(mock_email, context='created', user=loggedin_user)
    assert__refresh_response(resp)
    assert__task(expected, loggedin_user, service=s, data=[
        {
            'field': f,
            'value': expected_value,
        },
    ],
    expected_organisations=[organisation],
    )


def test__upload__upload_FileField__no_file(client, faker, loggedin_user, mock_email):
    s, f = faker.get_test_field_of_type(FieldType.get_file())

    organisation = faker.organisation().get_in_db()
    expected = faker.task().get()
    resp = _create_task_post(client, expected, service=s, organisations=[organisation])

    assert_emails_sent(mock_email, context='created', user=loggedin_user)
    assert__refresh_response(resp)
    assert__task(expected, loggedin_user, service=s, expected_organisations=[organisation])


def test__upload__upload_FileField(client, faker, loggedin_user, mock_email):
    s, f = faker.get_test_field_of_type(FieldType.get_file())

    field_data = {}

    fake_file = faker.fake_file()

    field_data[f.field_name] = fake_file.file_tuple()

    files = [
        {
            'field': f,
            'file': fake_file,
        }
    ]

    organisation = faker.organisation().get_in_db()
    expected = faker.task().get()
    resp = _create_task_post(client, expected, field_data=field_data, service=s, organisations=[organisation])

    assert_emails_sent(mock_email, context='created', user=loggedin_user)
    assert__refresh_response(resp)
    assert__task(expected, loggedin_user, files=files, service=s, expected_organisations=[organisation])


def test__upload__upload_MultiFileField__no_file(client, faker, loggedin_user, mock_email):
    s, f = faker.get_test_field_of_type(FieldType.get_multifile())

    organisation = faker.organisation().get_in_db()
    expected = faker.task().get()
    resp = _create_task_post(client, expected, service=s, organisations=[organisation])

    assert_emails_sent(mock_email, context='created', user=loggedin_user)
    assert__refresh_response(resp)
    assert__task(expected, loggedin_user, service=s, expected_organisations=[organisation])


@pytest.mark.parametrize(
    "n", [
        1,
        2,
        10,
    ],
)
def test__upload__upload_MultiFileField(client, faker, n, loggedin_user, mock_email):
    s, f = faker.get_test_field_of_type(FieldType.get_multifile())

    field_data = {
        f.field_name: [],
    }
    files = []

    for _ in range(n):
        fake_file = faker.fake_file()

        field_data[f.field_name].append(fake_file.file_tuple())

        files.append({
            'field': f,
            'file': fake_file,
        })

    organisation = faker.organisation().get_in_db()
    expected = faker.task().get()
    resp = _create_task_post(client, expected, field_data=field_data, service=s, organisations=[organisation])

    assert_emails_sent(mock_email, context='created', user=loggedin_user)
    assert__refresh_response(resp)
    assert__task(expected, loggedin_user, files=files, service=s, expected_organisations=[organisation])
