from lbrc_services.model.services import Task, TaskData
from flask import url_for
from lbrc_flask.forms.dynamic import FieldType
import pytest
from tests import lbrc_services_get
from lbrc_flask.pytest.asserts import assert__requires_login
from flask_api import status


def _url(task_id, external=True, prev=None):
    if prev == None:
        prev = url_for('ui.index', _external=True)

    return url_for('ui.edit_task', task_id=task_id, prev=prev, _external=external)


@pytest.mark.skip(reason="Flask_Login is adding extra parameters to URL")
def test__get__requires_login(client, faker):
    task = faker.get_test_task()

    assert__requires_login(client, _url(task.id, external=False))


def test__get__missing(client, faker, loggedin_user):
    resp = client.get(_url(task_id=999))
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test__get__not_service_owner_or_requestor(client, faker, loggedin_user):
    task = faker.get_test_task()

    resp = client.get(_url(task_id=task.id))
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.app_crsf(True)
def test__get__is_requestor(client, faker, loggedin_user):
    task = faker.get_test_task(requestor=loggedin_user)

    resp = lbrc_services_get(client, _url(task_id=task.id), loggedin_user, has_form=True)
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.app_crsf(True)
def test__get__is_service_owner(client, faker, loggedin_user):
    task = faker.get_test_owned_task(owner=loggedin_user)

    resp = lbrc_services_get(client, _url(task_id=task.id), loggedin_user, has_form=True)
    assert resp.status_code == status.HTTP_200_OK


def test__get__is_owner_of_other_service(client, faker, loggedin_user):
    user2 = faker.get_test_user()
    s_owned = faker.service_details(owners=[loggedin_user])
    task = faker.get_test_owned_task(owner=user2)

    resp = client.get(_url(task_id=task.id))
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.app_crsf(True)
def test__get__common_form_fields(client, faker, loggedin_user):
    task = faker.get_test_task(requestor=loggedin_user)

    resp = lbrc_services_get(client, _url(task_id=task.id), loggedin_user, has_form=True)
    assert resp.status_code == status.HTTP_200_OK

    assert resp.soup.find("select", id="organisation_id") is not None
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
    task = faker.get_test_task(service=s, requestor=loggedin_user)

    resp = lbrc_services_get(client, _url(task_id=task.id), loggedin_user, has_form=True)
    assert resp.status_code == status.HTTP_200_OK

    actual = resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name)
    assert actual is not None


@pytest.mark.app_crsf(True)
def test__update_task__boolean_field__True(client, faker, loggedin_user):
    ft = FieldType.get_boolean()
    s, f = faker.get_test_field_of_type(ft)
    task = faker.get_test_task(service=s, requestor=loggedin_user)
    td = faker.get_test_task_data(task=task, field=f, value='1')

    resp = lbrc_services_get(client, _url(task_id=task.id), loggedin_user, has_form=True)
    assert resp.status_code == status.HTTP_200_OK

    actual = resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name)
    assert actual is not None
    assert actual.has_attr('checked')


@pytest.mark.app_crsf(True)
def test__update_task__boolean_field__False(client, faker, loggedin_user):
    ft = FieldType.get_boolean()
    s, f = faker.get_test_field_of_type(ft)
    task = faker.get_test_task(service=s, requestor=loggedin_user)

    resp = lbrc_services_get(client, _url(task_id=task.id), loggedin_user, has_form=True)
    assert resp.status_code == status.HTTP_200_OK

    actual = resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name)
    assert actual is not None
    assert not actual.has_attr('checked')


@pytest.mark.app_crsf(True)
def test__update_task__integer_field__Value(client, faker, loggedin_user):
    ft = FieldType.get_integer()
    s, f = faker.get_test_field_of_type(ft)
    task = faker.get_test_task(service=s, requestor=loggedin_user)
    td = faker.get_test_task_data(task=task, field=f, value=1234)

    resp = lbrc_services_get(client, _url(task_id=task.id), loggedin_user, has_form=True)
    assert resp.status_code == status.HTTP_200_OK

    actual = resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name, value='1234')
    assert actual is not None


@pytest.mark.app_crsf(True)
def test__update_task__radio_field__Value(client, faker, loggedin_user):
    ft = FieldType.get_radio()
    s, f = faker.get_test_field_of_type(ft, choices='a|b|c')
    task = faker.get_test_task(service=s, requestor=loggedin_user)
    td = faker.get_test_task_data(task=task, field=f, value='a')

    resp = lbrc_services_get(client, _url(task_id=task.id), loggedin_user, has_form=True)
    assert resp.status_code == status.HTTP_200_OK

    actual = resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name)
    assert actual is not None

    for v in ['a', 'b', 'c']:
        assert actual.find('input', type='radio', value=v)

    assert actual.find('input', type='radio', value='a').has_attr('checked')


@pytest.mark.app_crsf(True)
def test__update_task__string_field__Value(client, faker, loggedin_user):
    ft = FieldType.get_string()
    s, f = faker.get_test_field_of_type(ft)
    task = faker.get_test_task(service=s, requestor=loggedin_user)
    td = faker.get_test_task_data(task=task, field=f, value='a')

    resp = lbrc_services_get(client, _url(task_id=task.id), loggedin_user, has_form=True)
    assert resp.status_code == status.HTTP_200_OK

    actual = resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name, value='a')
    assert actual is not None


@pytest.mark.app_crsf(True)
def test__update_task__textarea_field__Value(client, faker, loggedin_user):
    ft = FieldType.get_textarea()
    s, f = faker.get_test_field_of_type(ft)
    task = faker.get_test_task(service=s, requestor=loggedin_user)
    td = faker.get_test_task_data(task=task, field=f, value='a')

    resp = lbrc_services_get(client, _url(task_id=task.id), loggedin_user, has_form=True)
    assert resp.status_code == status.HTTP_200_OK

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
    task = faker.get_test_task(requestor=loggedin_user)
    url = url_for(endpoint)
    resp = lbrc_services_get(client, _url(task_id=task.id, prev=url), loggedin_user, has_form=True)
    assert resp.status_code == status.HTTP_200_OK

    assert resp.soup.find("a", href=url) is not None
    assert resp.soup.find("button", type="submit", string="Save") is not None
