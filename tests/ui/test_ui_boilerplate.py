import pytest
import re
from lbrc_flask.pytest.helpers import login
from lbrc_flask.pytest.asserts import assert_html_standards, assert_csrf_token, assert_basic_navigation
from tests import _get_test_request_type


@pytest.mark.parametrize(
    "path",
    [
        ("/"),
        ("/my_requests"),
        ("/my_jobs"),
        ("/request_type/<int:request_type_id>/create_request"),
    ],
)
def test__boilerplate__html_standards(client, faker, path):
    user = login(client, faker)

    path = re.sub(r"<int:request_type_id>", str(_get_test_request_type(faker).id), path)

    resp = client.get(path)

    assert_html_standards(resp.soup)
    assert_basic_navigation(resp.soup, user)


@pytest.mark.parametrize("path", [("/request_type/<int:request_type_id>/create_request")])
@pytest.mark.app_crsf(True)
def test__boilerplate__forms_csrf_token(client, faker, path):
    user = login(client, faker)

    path = re.sub(r"<int:request_type_id>", str(_get_test_request_type(faker).id), path)

    resp = client.get(path)

    assert_csrf_token(resp.soup)
