from tests.ui.create_request import _url
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

