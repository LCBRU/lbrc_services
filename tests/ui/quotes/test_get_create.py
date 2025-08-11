import http
from flask import url_for
from tests import lbrc_services_modal_get
from lbrc_flask.pytest.asserts import assert__requires_login, assert__requires_role


def _url(external=True):
    return url_for('ui.create_quote', _external=external)


def test__get__requires_login(client, faker):
    assert__requires_login(client, _url(external=False))


# def test__get__requires_quoter_role(client, faker, loggedin_user):
#     resp = assert__requires_role(client, _url())


def test__get__common_form_fields(client, faker, quoter_user):
    resp = lbrc_services_modal_get(client, _url(), quoter_user)
    assert resp.status_code == http.HTTPStatus.OK
    
    assert resp.soup.find("select", id="requestor_id") is not None
    assert resp.soup.find("input", type='text', id="name") is not None
    assert resp.soup.find("select", id="organisation_id") is not None
    assert resp.soup.find("input", type='text', id="organisation_description") is not None

    assert resp.soup.find("button", type="submit", string="Save") is not None
