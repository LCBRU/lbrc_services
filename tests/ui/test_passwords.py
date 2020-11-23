# -*- coding: utf-8 -*-

import pytest
from flask import url_for
from tests import login
from upload.model import User
from upload.database import db


@pytest.mark.parametrize(
    ["new_password", "valid"],
    [
        ("@Margaret", True),
        ("Margaret", False),
        ("@argaret", False),
        ("@MARGARET", False),
        ("@Ma", False),
    ],
)
def test__passwords__change(client, faker, new_password, valid):
    user = login(client, faker)

    password = "fred"

    user.password = password
    db.session.add(user)
    db.session.commit()

    resp = client.post(
        url_for("security.change_password"),
        data={
            "password": password,
            "new_password": new_password,
            "new_password_confirm": new_password,
        },
    )

    if valid:
        assert resp.status_code == 302
        assert resp.soup.find("div", "errors") is None
    else:
        assert resp.status_code == 200
        assert len(resp.soup.find("div", "errors").find_all("div")) > 0


def test__passwords__change_wrong_old_password(client, faker):
    user = login(client, faker)

    password = "fred"
    wrong_password = "freddy"
    new_password = "@Margaret"

    user.password = password
    db.session.add(user)
    db.session.commit()

    resp = client.post(
        url_for("security.change_password"),
        data={
            "password": wrong_password,
            "new_password": new_password,
            "new_password_confirm": new_password,
        },
    )

    assert resp.status_code == 200
    assert len(resp.soup.find("div", "errors").find_all("div")) > 0


def test__passwords__change_passwords_do_not_match(client, faker):
    user = login(client, faker)

    password = "fred"
    new_password = "@Margaret"
    wrong_new_password = "@Margare"

    user.password = password
    db.session.add(user)
    db.session.commit()

    resp = client.post(
        url_for("security.change_password"),
        data={
            "password": password,
            "new_password": new_password,
            "new_password_confirm": wrong_new_password,
        },
    )

    assert resp.status_code == 200
    assert len(resp.soup.find("div", "errors").find_all("div")) > 0
