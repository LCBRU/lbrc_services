from lbrc_services.model.services import Task, TaskData
from flask import url_for
from lbrc_flask.forms.dynamic import FieldType
import pytest
from tests import lbrc_services_get
from flask_api import status
from lbrc_flask.pytest.asserts import assert__requires_login, assert__requires_role


def _url(quote_id, external=True, prev=None):
    if prev == None:
        prev = url_for('ui.quotes', _external=True)

    return url_for('ui.edit_quote', quote_id=quote_id, prev=prev, _external=external)


@pytest.mark.skip(reason="Flask_Login is adding extra parameters to URL")
def test__get__requires_login(client, faker):
    quote = faker.get_test_quote()

    assert__requires_login(client, _url(quote.id, external=False))


def test__get__requires_quoter_role(client, faker, loggedin_user):
    quote = faker.get_test_quote()

    resp = assert__requires_role(client, _url(quote.id))


def test__get__missing(client, faker, quoter_user):
    resp = client.get(_url(quote_id=999))
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.app_crsf(True)
def test__get__common_form_fields(client, faker, quoter_user):
    quote = faker.get_test_quote()

    resp = lbrc_services_get(client, _url(quote.id), quoter_user)
    assert resp.status_code == status.HTTP_200_OK

    assert resp.soup.find("select", id="requestor_id") is not None
    assert resp.soup.find("input", type='text', id="name") is not None
    assert resp.soup.find("select", id="organisation_id") is not None
    assert resp.soup.find("input", type='text', id="organisation_description") is not None

    assert resp.soup.find("button", type="submit", string="Save") is not None
