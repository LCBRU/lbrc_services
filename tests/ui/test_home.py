import re
import pytest
from flask import url_for
from lbrc_flask.pytest.helpers import login
from lbrc_flask.database import db


def _url(**kwargs):
    return url_for('ui.index', _external=True, **kwargs)


def test__get__requires_login(client):
    resp = client.get(_url())
    assert resp.status_code == 302


@pytest.mark.parametrize(
    ["n"],
    [(0,), (1,), (2,), (10,)],
)
def test__requests_types(client, faker, n):
    user = login(client, faker)

    request_types = [faker.request_type_details() for _ in range(n)]
    db.session.add_all(request_types)
    db.session.commit()

    resp = client.get(_url())

    assert resp.status_code == 200
    content = resp.soup.find(id="content")
    assert len(content.find_all("a", "btn")) == n

    for rt in request_types:
        assert content.find("a", string=re.compile(rt.name)) is not None


