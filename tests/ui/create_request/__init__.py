from tests import get_test_service
from flask import url_for
from lbrc_flask.pytest.helpers import get_test_field, get_test_field_group


def _url(service_id, external=True, prev=None):
    if prev == None:
        prev = url_for('ui.index', _external=True)

    return url_for('ui.create_task', service_id=service_id, prev=prev, _external=external)


def get_test_field_of_type(faker, field_type, choices=None):
    fg = get_test_field_group(faker)
    s = get_test_service(faker, field_group=fg)
    f = get_test_field(faker, field_group=fg, field_type=field_type, choices=choices)
    return s,f
