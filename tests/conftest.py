from lbrc_services.security import init_authorization
import pytest
from lbrc_flask.pytest.faker import FieldsProvider
from lbrc_flask.pytest.helpers import login
from faker import Faker
from lbrc_flask.pytest.fixtures import *
from config import TestConfig
from lbrc_services import create_app
from lbrc_services.model import task_status_type_setup
from lbrc_services.model.security import ROLE_QUOTER
from lbrc_flask.security import add_user_to_role
from .faker import LbrcServicesProvider
from lbrc_flask.database import db
from lbrc_flask.forms.dynamic import create_field_types


@pytest.fixture(scope="function", autouse=True)
def standard_lookups(client, faker):
    return create_field_types()


@pytest.fixture(scope="function", autouse=True)
def task_status_setup(client, faker):
    return task_status_type_setup()


@pytest.fixture(scope="function", autouse=True)
def authorization_setup(client, faker):
    init_authorization()


@pytest.fixture(scope="function")
def loggedin_user(client, faker):
    return login(client, faker)


@pytest.fixture(scope="function")
def quoter_user(client, faker):
    u = login(client, faker)
    add_user_to_role(u, ROLE_QUOTER)
    db.session.commit()

    return u


@pytest.fixture(scope="function")
def app():
    return create_app(TestConfig)


@pytest.fixture(scope="function")
def faker():
    result = Faker("en_GB")
    result.add_provider(FieldsProvider)
    result.add_provider(LbrcServicesProvider)

    yield result
