import re
from tests import lbrc_services_get
from flask_api import status
from lbrc_flask.pytest.asserts import assert__requires_login
import pytest
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
    services = [faker.get_test_service() for _ in range(n)]

    resp = lbrc_services_get(client, _url(), loggedin_user)

    assert resp.status_code == status.HTTP_200_OK
    content = resp.soup.find(id="content")
    assert len(content.find_all("a", "btn")) == n

    for s in services:
        assert content.find("a", string=re.compile(s.name)) is not None


