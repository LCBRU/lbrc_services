from flask import url_for
from lbrc_flask.forms.dynamic import FieldType
from tests.ui.create_request import _url, get_test_field_of_type
import pytest
from tests import get_test_service
from lbrc_flask.pytest.helpers import login
from lbrc_flask.pytest.asserts import assert__form_standards, assert__html_standards, assert__requires_login
from lbrc_flask.database import db
from flask_api import status


def test__get__requires_login(client, faker):
    s = get_test_service(faker)
    assert__requires_login(client, _url(s.id, external=False))


def test__get__missing(client, faker):
    user = login(client, faker)

    resp = client.get(_url(service_id=999))
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.app_crsf(True)
def test__standards(client, faker):
    s = get_test_service(faker)
    assert__html_standards(client, faker, _url(service_id=s.id))
    assert__form_standards(client, faker, _url(service_id=s.id))


def test__get__common_form_fields(client, faker):
    user = login(client, faker)

    s = get_test_service(faker)
    resp = client.get(_url(service_id=s.id))
    assert resp.status_code == status.HTTP_200_OK

    assert resp.soup.find("select", id="organisation_id") is not None
    assert resp.soup.find("input", type='text', id="name") is not None
    assert resp.soup.find("input", type='text', id="organisation_description") is not None


def test__get__not_service_owner__cannot_select_requestor(client, faker):
    user = login(client, faker)

    s = get_test_service(faker)
    resp = client.get(_url(service_id=s.id))
    assert resp.status_code == status.HTTP_200_OK

    assert resp.soup.find("select", id="requestor_id") is None


def test__get__service_owner__can_select_requestor(client, faker):
    user = login(client, faker)

    s_owned = faker.service_details(owners=[user])
    db.session.add(s_owned)
    db.session.commit()

    s = get_test_service(faker)
    resp = client.get(_url(service_id=s.id))
    assert resp.status_code == status.HTTP_200_OK

    assert resp.soup.find("select", id="requestor_id") is not None


@pytest.mark.parametrize(
    "field_type_name", FieldType.all_field_type_name(),
)
def test__create_task__input_fields(client, faker, field_type_name):
    user = login(client, faker)

    ft = FieldType._get_field_type(field_type_name)
    s, f = get_test_field_of_type(faker, ft)

    resp = client.get(_url(service_id=s.id))
    assert resp.status_code == status.HTTP_200_OK

    print(resp.soup)
    assert resp.soup.find(ft.html_tag, type=ft.html_input_type, id=f.field_name) is not None


@pytest.mark.parametrize(
    "endpoint", [
        'ui.index',
        'ui.my_jobs',
        'ui.my_requests',
    ],
)
def test__get__cancel_button(client, faker, endpoint):
    user = login(client, faker)

    s = get_test_service(faker)
    url = url_for(endpoint)
    resp = client.get(_url(service_id=s.id, prev=url))
    assert resp.status_code == status.HTTP_200_OK

    assert resp.soup.find("a", href=url) is not None
