# -*- coding: utf-8 -*-

import json
import pytest
import datetime
import upload
import flask_security
from flask import Response
from flask.testing import FlaskClient
from bs4 import BeautifulSoup
from upload.database import db
from config import TestConfig, TestConfigCRSF


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime) or isinstance(o, datetime.date):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


class CustomResponse(Response):
    def __init__(self, baseObject):
        self.__class__ = type(
            baseObject.__class__.__name__, (self.__class__, baseObject.__class__), {}
        )
        self.__dict__ = baseObject.__dict__
        self._soup = None

    def get_json(self):
        return json.loads(self.get_data().decode("utf8"))

    @property
    def soup(self):
        if not self._soup:
            self._soup = BeautifulSoup(self.data, "html.parser")

        return self._soup


class CustomClient(FlaskClient):
    def __init__(self, *args, **kwargs):
        super(CustomClient, self).__init__(*args, **kwargs)

    def post_json(self, *args, **kwargs):

        kwargs["data"] = json.dumps(kwargs.get("data"), cls=DateTimeEncoder)
        kwargs["content_type"] = "application/json"

        return CustomResponse(super(CustomClient, self).post(*args, **kwargs))

    def get(self, *args, **kwargs):
        return CustomResponse(super(CustomClient, self).get(*args, **kwargs))

    def post(self, *args, **kwargs):
        return CustomResponse(super(CustomClient, self).post(*args, **kwargs))


def add_studies(faker):
    for _ in range(5):
        db.session.add(faker.study_details())

    db.session.commit()


def add_users(faker):
    for _ in range(5):
        db.session.add(faker.user_details())

    db.session.commit()


@pytest.yield_fixture(scope="function")
def app(faker):
    app = upload.create_app(TestConfig)
    app.test_client_class = CustomClient
    context = app.test_request_context()
    context.push()
    db.create_all()

    yield app

    context.pop()


@pytest.yield_fixture(scope="function")
def client(app):
    client = app.test_client()

    yield client


@pytest.yield_fixture(scope="function")
def client_with_crsf(faker):
    app = upload.create_app(TestConfigCRSF)
    app.test_client_class = CustomClient
    context = app.test_request_context()
    context.push()
    db.create_all()

    add_studies(faker)

    client = app.test_client()

    yield client

    context.pop()
