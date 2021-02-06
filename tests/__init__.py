from lbrc_flask.pytest.asserts import get_and_assert_standards
from flask import url_for


def lbrc_services_get(client, url, user, has_form=False):
    resp = get_and_assert_standards(client, url, user, has_form)

    assert resp.soup.nav is not None
    assert resp.soup.nav.find("a", href=url_for('ui.my_requests'), string="My Requests") is not None

    if user.service_owner:
        assert resp.soup.nav.find("a", href=url_for('ui.my_jobs'), string='My Jobs') is not None

    return resp
