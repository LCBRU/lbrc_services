import pytest
import http
from flask import url_for
from lbrc_flask.forms.dynamic import FieldType
from tests import lbrc_services_modal_get
from lbrc_flask.pytest.asserts import assert__requires_login


def _url(task_id, external=True, prev=None):
    return url_for('ui.edit_task_modal', task_id=task_id, prev=prev, _external=external)


def test__get__requires_login(client, faker):
    task = faker.task().get_in_db()

    assert__requires_login(client, _url(task.id, external=False))


def test__get__missing(client, faker, loggedin_user):
    resp = client.get(_url(task_id=999))
    assert resp.status_code == http.HTTPStatus.NOT_FOUND


def test__get__not_service_owner_or_requestor(client, faker, loggedin_user):
    task = faker.task().get_in_db()

    resp = client.get(_url(task_id=task.id))
    assert resp.status_code == http.HTTPStatus.FORBIDDEN


@pytest.mark.app_crsf(True)
def test__get__is_requestor(client, faker, loggedin_user):
    task = faker.task().get_in_db(requestor=loggedin_user)

    resp = lbrc_services_modal_get(client, _url(task_id=task.id), has_form=True)
    assert resp.status_code == http.HTTPStatus.OK


@pytest.mark.app_crsf(True)
def test__get__is_service_owner(client, faker, loggedin_user):
    s = faker.service().get_in_db(owners=[loggedin_user])
    task = faker.task().get_in_db(service=s)

    resp = lbrc_services_modal_get(client, _url(task_id=task.id), has_form=True)
    assert resp.status_code == http.HTTPStatus.OK


def test__get__is_owner_of_other_service(client, faker, loggedin_user):
    user2 = faker.user().get_in_db()
    s_owned = faker.service().get_in_db(owners=[loggedin_user])
    s_other = faker.service().get_in_db(owners=[user2])
    task = faker.task().get_in_db(service=s_other)

    resp = client.get(_url(task_id=task.id))
    assert resp.status_code == http.HTTPStatus.FORBIDDEN


@pytest.mark.app_crsf(True)
def test__get__common_form_fields(client, faker, loggedin_user):
    task = faker.task().get_in_db(requestor=loggedin_user)

    resp = lbrc_services_modal_get(client, _url(task_id=task.id), has_form=True)
    assert resp.status_code == http.HTTPStatus.OK

    assert resp.soup.find("select", id="organisations") is not None
    assert resp.soup.find("input", type='text', id="name") is not None
    assert resp.soup.find("input", type='text', id="organisation_description") is not None
    assert resp.soup.find("select", id="requestor_id") is None


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    "field_type_name", FieldType.all_field_type_name(),
)
def test__update_task__input_fields(client, faker, field_type_name, loggedin_user):
    ft = FieldType._get_field_type(field_type_name)
    s, f = faker.get_test_field_of_type(ft)
    task = faker.task().get_in_db(service=s, requestor=loggedin_user)

    resp = lbrc_services_modal_get(client, _url(task_id=task.id), has_form=True)
    assert resp.status_code == http.HTTPStatus.OK

    actual = resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name)
    assert actual is not None


@pytest.mark.app_crsf(True)
def test__update_task__boolean_field__True(client, faker, loggedin_user):
    ft = FieldType.get_boolean()
    s, f = faker.get_test_field_of_type(ft)
    task = faker.task().get_in_db(service=s, requestor=loggedin_user)
    td = faker.task_data().get_in_db(task=task, field=f, value='1')

    resp = lbrc_services_modal_get(client, _url(task_id=task.id), has_form=True)
    assert resp.status_code == http.HTTPStatus.OK

    actual = resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name)
    assert actual is not None
    assert actual.has_attr('checked')


@pytest.mark.app_crsf(True)
def test__update_task__boolean_field__False(client, faker, loggedin_user):
    ft = FieldType.get_boolean()
    s, f = faker.get_test_field_of_type(ft)
    task = faker.task().get_in_db(service=s, requestor=loggedin_user)

    resp = lbrc_services_modal_get(client, _url(task_id=task.id), has_form=True)
    assert resp.status_code == http.HTTPStatus.OK

    actual = resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name)
    assert actual is not None
    assert not actual.has_attr('checked')


@pytest.mark.app_crsf(True)
def test__update_task__integer_field__Value(client, faker, loggedin_user):
    ft = FieldType.get_integer()
    s, f = faker.get_test_field_of_type(ft)
    task = faker.task().get_in_db(service=s, requestor=loggedin_user)
    td = faker.task_data().get_in_db(task=task, field=f, value=1234)

    resp = lbrc_services_modal_get(client, _url(task_id=task.id), has_form=True)
    assert resp.status_code == http.HTTPStatus.OK

    actual = resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name, value='1234')
    assert actual is not None


@pytest.mark.app_crsf(True)
def test__update_task__radio_field__Value(client, faker, loggedin_user):
    ft = FieldType.get_radio()
    s, f = faker.get_test_field_of_type(ft, choices='a|b|c')
    task = faker.task().get_in_db(service=s, requestor=loggedin_user)
    td = faker.task_data().get_in_db(task=task, field=f, value='a')

    resp = lbrc_services_modal_get(client, _url(task_id=task.id), has_form=True)
    assert resp.status_code == http.HTTPStatus.OK

    actual = resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name)
    assert actual is not None

    for v in ['a', 'b', 'c']:
        assert actual.find('input', type='radio', value=v)

    assert actual.find('input', type='radio', value='a').has_attr('checked')


@pytest.mark.app_crsf(True)
def test__update_task__string_field__Value(client, faker, loggedin_user):
    ft = FieldType.get_string()
    s, f = faker.get_test_field_of_type(ft)
    task = faker.task().get_in_db(service=s, requestor=loggedin_user)
    td = faker.task_data().get_in_db(task=task, field=f, value='a')

    resp = lbrc_services_modal_get(client, _url(task_id=task.id), has_form=True)
    assert resp.status_code == http.HTTPStatus.OK

    actual = resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name, value='a')
    assert actual is not None


@pytest.mark.app_crsf(True)
def test__update_task__textarea_field__Value(client, faker, loggedin_user):
    ft = FieldType.get_textarea()
    s, f = faker.get_test_field_of_type(ft)
    task = faker.task().get_in_db(service=s, requestor=loggedin_user)
    td = faker.task_data().get_in_db(task=task, field=f, value='a')

    resp = lbrc_services_modal_get(client, _url(task_id=task.id), has_form=True)
    assert resp.status_code == http.HTTPStatus.OK

    actual = resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name)
    assert actual.contents[0].strip() == 'a'


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    "endpoint", [
        'ui.index',
        'ui.my_jobs',
        'ui.my_requests',
    ],
)
def test__get__buttons(client, faker, endpoint, loggedin_user):
    task = faker.task().get_in_db(requestor=loggedin_user)
    url = url_for(endpoint)
    resp = lbrc_services_modal_get(client, _url(task_id=task.id, prev=url), has_form=True)
    assert resp.status_code == http.HTTPStatus.OK

    assert resp.soup.find("a", string="Cancel") is not None
    assert resp.soup.find("button", type="submit", string="Save") is not None
