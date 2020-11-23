# -*- coding: utf-8 -*-

import pytest
import re
import os
from itertools import cycle
from flask import url_for
from tests import login
from upload.database import db


def test__study_list__no_studies__no_display(client, faker):
    login(client, faker)

    resp = client.get("/")

    assert resp.status_code == 200
    assert resp.soup.find("h2", string="Owned Studies") is None
    assert resp.soup.find("h2", string="Collaborating Studies") is None
    assert len(resp.soup.find_all("table", "table study_list")) == 0


def test__study_list__owns_1_study_redirects(client, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)

    db.session.add(study)
    db.session.commit()

    resp = client.get("/")

    assert resp.status_code == 302
    assert resp.location == (url_for("ui.study", study_id=study.id, _external=True))


@pytest.mark.parametrize("study_count", [(2), (3)])
def test__study_list__owns_mult_studies(client, faker, study_count):
    user = login(client, faker)
    studies = []

    for _ in range(study_count):
        study = faker.study_details()
        study.owners.append(user)
        studies.append(study)

        db.session.add(study)

    db.session.commit()

    resp = client.get("/")

    assert resp.status_code == 200
    assert resp.soup.find("h2", string="Owned Studies") is not None
    assert resp.soup.find("h2", string="Collaborating Studies") is None
    assert len(resp.soup.select("table.study_list")) == 1
    assert len(resp.soup.select("table.study_list > tbody > tr")) == study_count

    for s in studies:
        assert resp.soup.find("a", href=url_for("ui.study", study_id=s.id)) is not None
        assert (
            resp.soup.find("a", href=url_for("ui.study_csv", study_id=s.id)) is not None
        )
        assert resp.soup.find("td", string=s.name) is not None


@pytest.mark.parametrize(
    ["outstanding", "completed", "deleted"],
    [(2, 2, 0), (3, 0, 4), (2, 2, 2), (3, 0, 0)],
)
def test__study_list__owned_study__upload_count(
    client, faker, outstanding, completed, deleted
):
    user = login(client, faker)

    user2 = faker.user_details()
    db.session.add(user2)

    study = faker.study_details()
    study.owners.append(user)
    study2 = faker.study_details()
    study2.owners.append(user)

    db.session.add(study)
    db.session.add(study2)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([user, user2])

    for _ in range(outstanding):
        u = faker.upload_details()
        u.completed = False
        u.study = study
        u.uploader = next(users)

        db.session.add(u)

    for _ in range(completed):
        u = faker.upload_details()
        u.completed = True
        u.study = study
        u.uploader = next(users)

        db.session.add(u)

    for _ in range(deleted):
        u = faker.upload_details()
        u.completed = False
        u.deleted = True
        u.study = study
        u.uploader = next(users)

        db.session.add(u)

    db.session.commit()

    resp = client.get("/")

    assert resp.status_code == 200

    study_row = resp.soup.find("td", string=study.name).parent

    assert study_row.find_all("td")[2].string == str(outstanding + completed)
    assert study_row.find_all("td")[3].string == str(outstanding)


def test__study_list__coll_1_study_redirects(client, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.collaborators.append(user)

    db.session.add(study)
    db.session.commit()

    resp = client.get("/")

    assert resp.status_code == 302
    assert resp.location == (
        url_for("ui.study_my_uploads", study_id=study.id, _external=True)
    )


@pytest.mark.parametrize("study_count", [(2), (3)])
def test__study_list__colls_mult_studies(client, faker, study_count):
    user = login(client, faker)
    studies = []

    for _ in range(study_count):
        study = faker.study_details()
        study.collaborators.append(user)
        studies.append(study)

        db.session.add(study)

    db.session.commit()

    resp = client.get("/")

    assert resp.status_code == 200
    assert resp.soup.find("h2", string="Owned Studies") is None
    assert resp.soup.find("h2", string="Collaborating Studies") is not None
    assert len(resp.soup.select("table.study_list")) == 1
    assert len(resp.soup.select("table.study_list > tbody > tr")) == study_count

    for s in studies:
        assert (
            resp.soup.find("a", href=url_for("ui.study_my_uploads", study_id=s.id))
            is not None
        )
        assert (
            resp.soup.find("a", href=url_for("ui.upload_data", study_id=s.id))
            is not None
        )
        assert resp.soup.find("td", string=s.name) is not None


@pytest.mark.parametrize(
    ["me", "someone_else", "deleted"], [(2, 2, 0), (3, 0, 4), (2, 2, 4), (3, 0, 0)]
)
def test__study_list__owned_study__upload_count(
    client, faker, me, someone_else, deleted
):
    user = login(client, faker)

    user2 = faker.user_details()
    db.session.add(user2)

    study = faker.study_details()
    study.collaborators.append(user)
    study2 = faker.study_details()
    study2.collaborators.append(user)

    db.session.add(study)
    db.session.add(study2)

    for _ in range(me):
        u = faker.upload_details()
        u.completed = False
        u.study = study
        u.uploader = user

        db.session.add(u)

    for _ in range(someone_else):
        u = faker.upload_details()
        u.completed = True
        u.study = study
        u.uploader = user2

        db.session.add(u)

    # Cycle is used to alternately allocate
    # the uploads to a different user
    # thus we can test that we can see
    # uploads by users other than ourselves
    users = cycle([user, user2])

    for _ in range(deleted):
        u = faker.upload_details()
        u.completed = False
        u.deleted = True
        u.study = study
        u.uploader = next(users)

        db.session.add(u)

    db.session.commit()

    resp = client.get("/")

    assert resp.status_code == 200

    study_row = resp.soup.find("td", string=study.name).parent

    assert study_row.find_all("td")[2].string == str(me)
