from lbrc_flask.pytest.faker import LbrcDynaicFormFakerProvider
import pytest
from faker import Faker
from lbrc_flask.pytest.fixtures import *
from config import TestConfig
from lbrc_requests import create_app
from .faker import LbrcRequestsFakerProvider


@pytest.fixture(scope="function")
def app():
    return create_app(TestConfig)


@pytest.yield_fixture(scope="function")
def faker():
    result = Faker("en_GB")
    result.add_provider(LbrcDynaicFormFakerProvider)
    result.add_provider(LbrcRequestsFakerProvider)

    yield result

