import http
from flask import url_for
from lbrc_flask.pytest.asserts import assert__refresh_response, assert__requires_login, assert__requires_role, assert__error__required_field_modal, assert__error__required_field_modal
from lbrc_services.model.services import Organisation
from tests.ui.quotes import assert__quote, post_quote


def _url(external=True):
    return url_for('ui.create_quote', _external=external)


def _create_post(client, quote):
    return post_quote(client,  _url(), quote)


def test__post__requires_login(client, faker):
    assert__requires_login(client, _url(external=False), post=True)


def test__post__requires_quoter_role(client, faker, loggedin_user):
    resp = assert__requires_role(client, _url(), post=True)


def test__create_task__with_all_values(client, faker, quoter_user):
    expected = faker.quote_details()

    resp = _create_post(client, expected)

    assert__refresh_response(resp)
    assert__quote(expected, quoter_user)


def test__create_task__empty_name(client, faker, quoter_user):
    expected = faker.quote_details(name='')

    resp = _create_post(client, expected)

    assert resp.status_code == http.HTTPStatus.OK
    assert__error__required_field_modal(resp.soup, "Quote Title")


def test__create_task__empty_organisation(client, faker, quoter_user):
    expected = faker.quote_details()
    expected.organisation_id = None

    resp = _create_post(client, expected)

    assert resp.status_code == http.HTTPStatus.OK
    assert__error__required_field_modal(resp.soup, "organisation")


def test__create_task__empty_requestor__uses_current_user(client, faker, quoter_user):
    expected = faker.quote_details()
    expected.requestor_id = None

    resp = _create_post(client, expected)

    assert__refresh_response(resp)
    expected.requestor_id = quoter_user.id
    assert__quote(expected, quoter_user)


def test__create_task__empty_organisation_description__when_organisation_is_other(client, faker, quoter_user):
    expected = faker.quote_details(organisation=Organisation.get_other())

    resp = _create_post(client, expected)

    assert resp.status_code == http.HTTPStatus.OK
    assert__error__required_field_modal(resp.soup, "organisation description")
