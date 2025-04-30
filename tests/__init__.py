from dotenv import load_dotenv

# Load environment variables from '.env' file.
load_dotenv()

import re
from lbrc_flask.pytest.asserts import get_and_assert_standards
from flask import url_for

from lbrc_services.model.security import ROLE_QUOTER


def lbrc_services_get(client, url, user, has_form=False):
    resp = get_and_assert_standards(client, url, user, has_form)

    assert resp.soup.nav is not None
    assert resp.soup.nav.find("a", href=url_for('ui.my_requests'), string=re.compile("My Requests")) is not None

    if user.service_owner:
        assert resp.soup.nav.find("a", href=url_for('ui.my_jobs'), string=re.compile('My Jobs')) is not None
    else:
        assert resp.soup.nav.find("a", href=url_for('ui.my_jobs'), string=re.compile('My Jobs')) is None
    
    if user.has_role(ROLE_QUOTER):
        assert resp.soup.nav.find("a", href=url_for('ui.quotes'), string=re.compile("Quotes")) is not None
    else:
        assert resp.soup.nav.find("a", href=url_for('ui.quotes'), string=re.compile('Quotes')) is None

    return resp
