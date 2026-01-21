import re
import pytest
import http
from tests import lbrc_services_get
from lbrc_flask.pytest.asserts import assert__requires_login
from flask import url_for


def _url(external=True, **kwargs):
    return url_for('ui.index', _external=external, **kwargs)


def test__get__requires_login(client):
    assert__requires_login(client, _url(external=False))


@pytest.mark.parametrize(
    ["n"],
    [(0,), (1,), (2,), (10,)],
)
def test__services(client, faker, n, loggedin_user):
    services =faker.service().get_list(save=True, item_count=n, owners=[loggedin_user])

    resp = lbrc_services_get(client, _url(), loggedin_user)

    print(resp.soup)

    assert resp.status_code == http.HTTPStatus.OK
    content = resp.soup.find('ul', "cards")
    assert len(content.find_all("li")) == n

    for s in services:
        assert content.find("a", string=re.compile(s.name)) is not None


