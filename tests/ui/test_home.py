import re
from lbrc_flask.pytest.asserts import assert__requires_login
import pytest
from flask import url_for
from lbrc_flask.pytest.helpers import login
from lbrc_flask.database import db


def _url(external=True, **kwargs):
    return url_for('ui.index', _external=external, **kwargs)


def test__get__requires_login(client):
    assert__requires_login(client, _url(external=False))


@pytest.mark.parametrize(
    ["n"],
    [(0,), (1,), (2,), (10,)],
)
def test__services(client, faker, n):
    user = login(client, faker)

    services = [faker.service_details() for _ in range(n)]
    db.session.add_all(services)
    db.session.commit()

    resp = client.get(_url())

    assert resp.status_code == 200
    content = resp.soup.find(id="content")
    assert len(content.find_all("a", "btn")) == n

    for s in services:
        assert content.find("a", string=re.compile(s.name)) is not None


