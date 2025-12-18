import http
from flask import url_for
from lbrc_services.model.services import Organisation
from lbrc_flask.pytest.asserts import assert__error__required_field_modal, assert__refresh_response, assert__requires_login
from tests.ui.quotes import assert__quote, post_quote


def _url(quote_id, external=True, prev=None):
    if prev == None:
        prev = url_for('ui.quotes', _external=True)

    return url_for('ui.edit_quote', quote_id=quote_id, prev=prev, _external=external)


def _edit_post(client, quote):
    return post_quote(client,  _url(quote_id=quote.id), quote)


def test__post__requires_login(client, faker):
    quote = faker.quote().get_in_db()

    assert__requires_login(client, _url(quote_id=quote.id, external=False), post=True)


def test__post__missing(client, faker, quoter_user):
    resp = client.post(_url(quote_id=999))
    assert resp.status_code == http.HTTPStatus.NOT_FOUND


def test__update__with_all_values(client, faker, quoter_user):
    quote = faker.quote().get_in_db(requestor=quoter_user)

    resp = _edit_post(client, quote)

    assert__refresh_response(resp)
    assert__quote(quote, quoter_user)


def test__update__empty_name(client, faker, quoter_user):
    quote = faker.quote().get_in_db(requestor=quoter_user)
    quote.name = ''

    resp = _edit_post(client, quote)

    assert resp.status_code == http.HTTPStatus.OK
    assert__error__required_field_modal(resp.soup, "Quote Title")


def test__create_task__empty_organisation(client, faker, quoter_user):
    expected = faker.quote().get_in_db(requestor=quoter_user)
    expected.organisation_id = None

    resp = _edit_post(client, expected)

    assert resp.status_code == http.HTTPStatus.OK
    assert__error__required_field_modal(resp.soup, "organisation")


def test__create_task__empty_organisation_description__when_organisation_is_other(client, faker, quoter_user):
    expected = faker.quote().get_in_db(requestor=quoter_user, organisation=Organisation.get_other())

    resp = _edit_post(client, expected)

    assert resp.status_code == http.HTTPStatus.OK
    assert__error__required_field_modal(resp.soup, "organisation description")
