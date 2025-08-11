import pytest
import re
import http
from datetime import datetime
from flask import url_for
from lbrc_services.model.quotes import QuoteStatusType
from lbrc_services.model.services import Organisation
from tests import lbrc_services_get
from lbrc_flask.pytest.asserts import assert__requires_login, assert__search_html, assert__select, assert__requires_role
from lbrc_services.ui.forms import QuoteSearchForm, _get_combined_quote_status_type_choices
from lbrc_flask.pytest.asserts import assert__select, assert__page_navigation


def _url(external=True, **kwargs):
    return url_for('ui.quotes', _external=external, **kwargs)


def test__get__requires_login(client):
    assert__requires_login(client, _url(external=False))


def test__get__requires_quoter_role(client, loggedin_user):
    assert__requires_role(client, _url(external=False))


def _get(client, url, loggedin_user, has_form):
    resp = lbrc_services_get(client, url, loggedin_user, has_form)

    assert__search_html(resp.soup, clear_url=_url(external=False))

    assert__select(soup=resp.soup, id='quote_status_type_id', options=_get_combined_quote_status_type_choices())

    return resp


@pytest.mark.app_crsf(True)
@pytest.mark.parametrize(
    "quotes",
    [0, 1, 5],
)
def test__quotes(client, faker, quotes, quoter_user):
    my_quotes = faker.get_test_quotes(requestor=quoter_user, count=quotes)

    resp = _get(client, _url(), quoter_user, has_form=True)

    assert_results(resp, my_quotes)


@pytest.mark.app_crsf(True)
def test__quotes__search__name(client, faker, quoter_user):
    matching = faker.get_test_quotes(requestor=quoter_user, name='Mary')
    non_matching = faker.get_test_quotes(requestor=quoter_user, name='Joseph')

    resp = _get(client, _url(search='ar'), quoter_user, has_form=True)

    assert_results(resp, matching)


@pytest.mark.app_crsf(True)
def test__quotes__search__task_status_type(client, faker, quoter_user):
    matching = faker.get_test_quotes(requestor=quoter_user, current_status_type=QuoteStatusType.get_awaiting_approval())
    non_matching = faker.get_test_quotes(requestor=quoter_user, current_status_type=QuoteStatusType.get_charged())

    resp = _get(client, _url(quote_status_type_id=QuoteStatusType.get_awaiting_approval().id), quoter_user, has_form=True)

    assert_results(resp, matching)


@pytest.mark.app_crsf(True)
def test__quotes__search__organisation(client, faker, quoter_user):
    matching = faker.get_test_quotes(requestor=quoter_user, organisation=Organisation.get_organisation(Organisation.CARDIOVASCULAR))
    non_matching = faker.get_test_quotes(requestor=quoter_user, organisation=Organisation.get_organisation(Organisation.LIFESTYLE))

    resp = _get(client, _url(organisation_id=Organisation.get_organisation(Organisation.CARDIOVASCULAR).id), quoter_user, has_form=True)

    assert_results(resp, matching)


@pytest.mark.app_crsf(True)
def test__quotes__search__created_from(client, faker, quoter_user):
    matching = faker.get_test_quotes(requestor=quoter_user, created_date=datetime(2020, 1, 1))
    non_matching = faker.get_test_quotes(requestor=quoter_user, created_date=datetime(2019, 12, 31))

    resp = _get(client, _url(created_date_from='2020-01-01'), quoter_user, has_form=True)

    assert_results(resp, matching)


@pytest.mark.app_crsf(True)
def test__quotes__search__created_to(client, faker, quoter_user):
    non_matching = faker.get_test_quotes(requestor=quoter_user, created_date=datetime(2020, 1, 1))
    matching = faker.get_test_quotes(requestor=quoter_user, created_date=datetime(2019, 12, 31))

    resp = _get(client, _url(created_date_to='2019-12-31'), quoter_user, has_form=True)

    assert_results(resp, matching)


@pytest.mark.parametrize(
    "quote_count",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__quotes__pages(client, faker, quote_count, quoter_user):
    quotes = faker.get_test_quotes(count=quote_count)

    assert__page_navigation(client, 'ui.quotes', {'_external': False}, quote_count, form=QuoteSearchForm())


@pytest.mark.parametrize(
    "quote_count",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__quotes__search__name__pages(client, faker, quote_count, quoter_user):
    matching = faker.get_test_quotes(name='Mary', requestor=quoter_user, count=quote_count)
    unmatching = faker.get_test_quotes(name='Joseph', requestor=quoter_user, count=100)

    assert__page_navigation(client, 'ui.quotes', {'_external': False, 'search': 'ar'}, quote_count, form=QuoteSearchForm())


@pytest.mark.parametrize(
    "quote_count",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__quotes__search__quote_status__pages(client, faker, quote_count, quoter_user):
    matching = faker.get_test_quotes(current_status_type=QuoteStatusType.get_paid(), requestor=quoter_user, count=quote_count)
    unmatching = faker.get_test_quotes(current_status_type=QuoteStatusType.get_awaiting_approval(), requestor=quoter_user, count=100)

    assert__page_navigation(client, 'ui.quotes', {'_external': False, 'quote_status_type_id': QuoteStatusType.get_paid().id}, quote_count, form=QuoteSearchForm())


@pytest.mark.parametrize(
    "quote_count",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__quotes__search__organisation__pages(client, faker, quote_count, quoter_user):
    matching = faker.get_test_quotes(organisation=Organisation.get_organisation(Organisation.CARDIOVASCULAR), requestor=quoter_user, count=quote_count)
    unmatching = faker.get_test_quotes(organisation=Organisation.get_organisation(Organisation.LIFESTYLE), requestor=quoter_user, count=100)

    assert__page_navigation(client, 'ui.quotes', {'_external': False, 'organisation_id': Organisation.get_organisation(Organisation.CARDIOVASCULAR).id}, quote_count, form=QuoteSearchForm())


@pytest.mark.parametrize(
    "quote_count",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__quotes__search__created_from__pages(client, faker, quoter_user, quote_count):
    matching = faker.get_test_quotes(requestor=quoter_user, created_date=datetime(2020, 1, 1), count=quote_count)
    non_matching = faker.get_test_quotes(requestor=quoter_user, created_date=datetime(2019, 12, 31), count=100)

    assert__page_navigation(client, 'ui.quotes', {'_external': False, 'created_date_from': '2020-01-01'}, quote_count, form=QuoteSearchForm())


@pytest.mark.parametrize(
    "quote_count",
    [0, 1, 5, 6, 11, 16, 21, 26, 31, 101],
)
def test__quotes__search__created_to__pages(client, faker, quoter_user, quote_count):
    non_matching = faker.get_test_quotes(requestor=quoter_user, created_date=datetime(2020, 1, 1), count=100)
    matching = faker.get_test_quotes(requestor=quoter_user, created_date=datetime(2019, 12, 31), count=quote_count)

    assert__page_navigation(client, 'ui.quotes', {'_external': False, 'created_date_to': '2019-12-31'}, quote_count, form=QuoteSearchForm())


def assert_results(resp, matches):
    assert resp.status_code == http.HTTPStatus.OK
    assert len(resp.soup.find_all("li", "list-group-item")) == len(matches)

    for u, li in zip(reversed(matches), resp.soup.find_all("li", "list-group-item")):
        quote_matches_li(u, li)


def quote_matches_li(quote, li):

    assert li.find("h1").find(string=re.compile(quote.name)) is not None
    assert li.find("h2").find(string=re.compile(quote.requestor.full_name)) is not None
