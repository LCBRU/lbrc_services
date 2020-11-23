# -*- coding: utf-8 -*-

import pytest
import re
import os
import csv
from io import StringIO
from itertools import cycle
from flask import url_for
from tests import login
from upload.database import db


@pytest.mark.parametrize("upload_count", [(0), (2), (3), (100)])
def test__study_csv__download(client, faker, upload_count):
    user = login(client, faker)
    uploads = []

    study = faker.study_details()
    study.owners.append(user)

    for _ in range(upload_count):
        upload = faker.upload_details()
        upload.study = study
        upload.uploader = user
        uploads.append(upload)

        db.session.add(upload)

    db.session.commit()

    resp = client.get(url_for("ui.study_csv", study_id=study.id))

    assert resp.status_code == 200

    decoded_content = resp.data.decode("utf-8")

    rows = list(csv.reader(StringIO(decoded_content), delimiter=","))

    assert rows[0] == [
        "upload_id",
        "study_name",
        "study_number",
        "uploaded_by",
        "date_created",
    ]

    for u, row in zip(uploads, rows[1:]):
        assert row[0] == str(u.id)
        assert row[1] == u.study.name
        assert row[2] == u.study_number
        assert row[3] == u.uploader.full_name
        assert row[4] == u.date_created.strftime("%Y-%m-%d %H:%M:%S.%f")
