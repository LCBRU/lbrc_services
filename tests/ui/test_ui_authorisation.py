# -*- coding: utf-8 -*-

import pytest
from tests import login
from upload.database import db


def test_missing_route(client):
    resp = client.get("/uihfihihf")
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "path",
    [
        ("/static/css/main.css"),
        ("/static/img/nihr-logo-70.png"),
        ("/static/img/cropped-favicon-32x32.png"),
        ("/static/img//cropped-favicon-192x192.png"),
        ("/static/img//cropped-favicon-180x180.png"),
        ("/static/img//cropped-favicon-270x270.png"),
        ("/static/favicon.ico"),
    ],
)
def test_url_exists_without_login(client, path):
    resp = client.get(path)

    assert resp.status_code == 200


@pytest.mark.parametrize(
    "path",
    [
        ("/"),
        ("/study/1"),
        ("/study/1/my_uploads"),
        ("/study/1/upload"),
        ("/upload/file/1"),
        ("/study/1/csv"),
    ],
)
def test_url_requires_login_get(client, path):
    resp = client.get(path)
    assert resp.status_code == 302


@pytest.mark.parametrize("path", [("/upload_delete"), ("/upload_complete")])
def test_url_requires_login_post(client, path):
    resp = client.post(path)
    assert resp.status_code == 302


@pytest.mark.parametrize("path", [("/")])
def test_url_requires_login_common_page(client, faker, path):
    login(client, faker)
    resp = client.get(path)
    assert resp.status_code == 200


@pytest.mark.parametrize("path", [("/study/{}"), ("/study/{}/csv")])
def test_must_be_study_owner_is(client, path, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)
    db.session.add(study)
    db.session.commit()

    resp = client.get(path.format(study.id))
    assert resp.status_code == 200


@pytest.mark.parametrize("path", [("/study/{}"), ("/study/{}/csv")])
def test_must_be_study_owner_isnt(client, path, faker):
    login(client, faker)

    study = faker.study_details()
    db.session.add(study)
    db.session.commit()

    resp = client.get(path.format(study.id))
    assert resp.status_code == 403


@pytest.mark.parametrize("path", [("/study/{}/my_uploads"), ("/study/{}/upload")])
def test_must_be_study_collaborator_is(client, path, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.collaborators.append(user)
    db.session.add(study)
    db.session.commit()

    resp = client.get(path.format(study.id))
    assert resp.status_code == 200


@pytest.mark.parametrize("path", [("/study/{}/my_uploads"), ("/study/{}/upload")])
def test_must_be_study_collaborator_isnt(client, path, faker):
    login(client, faker)

    study = faker.study_details()
    db.session.add(study)
    db.session.commit()

    resp = client.get(path.format(study.id))
    assert resp.status_code == 403
