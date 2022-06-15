import pytest
from flask import url_for
from tests import lbrc_services_get
from lbrc_flask.pytest.asserts import assert__requires_login, assert__requires_role
from flask_api import status


def _url(external=True, prev=None):
    if prev == None:
        prev = url_for('ui.index', _external=True)

    return url_for('ui.create_quote', prev=prev, _external=external)


@pytest.mark.skip(reason="Flask_Login is adding extra parameters to URL")
def test__get__requires_login(client, faker):
    assert__requires_login(client, _url(external=False))


def test__get__requires_quoter_role(client, faker, loggedin_user):
    resp = assert__requires_role(client, _url())


def test__get__common_form_fields(client, faker, quoter_user):
    resp = lbrc_services_get(client, _url(), quoter_user)
    assert resp.status_code == status.HTTP_200_OK

    assert resp.soup.find("select", id="requestor_id") is not None
    assert resp.soup.find("input", type='text', id="name") is not None
    assert resp.soup.find("select", id="organisation_id") is not None
    assert resp.soup.find("input", type='text', id="organisation_description") is not None

    assert resp.soup.find("button", type="submit", string="Save") is not None
