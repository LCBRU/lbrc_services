# -*- coding: utf-8 -*-

import pytest
import re
from upload.database import db
from tests import login, add_content_for_all_areas


@pytest.mark.parametrize(
    "path",
    [
        ("/"),
        ("/study/<int:study_id>"),
        ("/study/<int:study_id>/my_uploads"),
        ("/study/<int:study_id>/upload"),
    ],
)
def test__boilerplate__html_standards(client, faker, path):
    user = login(client, faker)

    study, upload = add_content_for_all_areas(faker, user)

    path = re.sub(r"<int:study_id>", str(study.id), path)
    path = re.sub(r"<int:study_id>", str(upload.id), path)

    resp = client.get(path)

    assert resp.soup.html is not None
    assert resp.soup.html["lang"] == "en"
    assert resp.soup.head is not None
    assert (
        resp.soup.find(
            lambda tag: tag.name == "meta"
            and tag.has_attr("charset")
            and tag["charset"] == "utf-8"
        )
        is not None
    )
    assert resp.soup.title is not None
    assert resp.soup.body is not None


@pytest.mark.parametrize("path", [("/study/{}/upload")])
def test__boilerplate__forms_csrf_token(client_with_crsf, faker, path):
    client = client_with_crsf
    user = login(client, faker)

    study = faker.study_details()
    study.collaborators.append(user)

    db.session.add(study)
    db.session.commit()

    resp = client.get(path.format(study.id))

    assert (
        resp.soup.find("input", {"name": "csrf_token"}, type="hidden", id="csrf_token")
        is not None
    )


@pytest.mark.parametrize(
    "path",
    [
        ("/"),
        ("/study/<int:study_id>"),
        ("/study/<int:study_id>/my_uploads"),
        ("/study/<int:study_id>/upload"),
    ],
)
def test__boilerplate__basic_navigation(client, faker, path):
    user = login(client, faker)

    study, upload = add_content_for_all_areas(faker, user)

    path = re.sub(r"<int:study_id>", str(study.id), path)
    path = re.sub(r"<int:study_id>", str(upload.id), path)

    resp = client.get(path)

    resp.soup.nav is not None
    resp.soup.nav.find("a", href="/") is not None
    resp.soup.nav.find("a", string=user.full_name) is not None
    resp.soup.nav.find("a", string=user.full_name) is not None
    resp.soup.nav.find("a", href="/change") is not None
    resp.soup.nav.find("a", href="/logout") is not None
