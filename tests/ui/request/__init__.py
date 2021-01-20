from lbrc_flask.database import db
from tests import get_test_service
from lbrc_flask.pytest.helpers import get_test_field, get_test_field_group


def get_test_field_of_type(faker, field_type, choices=None):
    fg = get_test_field_group(faker)
    s = get_test_service(faker, field_group=fg)
    f = get_test_field(faker, field_group=fg, field_type=field_type, choices=choices)
    return s,f
