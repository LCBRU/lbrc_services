from lbrc_flask.pytest.faker import LbrcDynaicFormFakerProvider
from lbrc_flask.pytest.helpers import login
import pytest
from faker import Faker
from lbrc_flask.pytest.fixtures import *
from config import TestConfig
from lbrc_services import create_app
from .faker import LbrcServicesFakerProvider


@pytest.fixture(scope="function")
def loggedin_user(client, faker):
    return login(client, faker)


@pytest.fixture(scope="function")
def app():
    return create_app(TestConfig)


@pytest.fixture(scope="function")
def faker():
    result = Faker("en_GB")
    result.add_provider(LbrcDynaicFormFakerProvider)
    result.add_provider(LbrcServicesFakerProvider)

    yield result

