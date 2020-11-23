# -*- coding: utf-8 -*-

import re
import csv
import pytest
import os
from io import BytesIO
from itertools import cycle
from flask import url_for
from tests import login, add_field_types
from upload.database import db
from upload.ui import get_upload_filepath
from upload.model import Upload, FieldType, Field, UploadFile, UploadData


def test__upload__file_download(client, faker):
    path = "/upload/file/{}"
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)

    file_field = faker.field_details("FileField")
    file_field.study = study
    file_field.order = 1

    upload = faker.upload_details()
    upload.study = study

    upload_file = faker.upload_file_details()
    upload_file.upload = upload
    upload_file.field = file_field

    db.session.add(study)
    db.session.add(file_field)
    db.session.add(upload)
    db.session.add(upload_file)
    db.session.commit()

    filename = get_upload_filepath(upload_file)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        f.write(faker.text())

    resp = client.get(path.format(upload_file.id))

    os.unlink(filename)
    os.rmdir(os.path.dirname(filename))

    assert resp.status_code == 200


def test__upload___must_be_upload_study_owner_isnt(client, faker):
    login(client, faker)

    path = "/upload/file/{}"

    study = faker.study_details()

    file_field = faker.field_details("FileField")
    file_field.study = study
    file_field.order = 1

    upload = faker.upload_details()
    upload.study = study

    upload_file = faker.upload_file_details()
    upload_file.upload = upload
    upload_file.field = file_field

    db.session.add(study)
    db.session.add(file_field)
    db.session.add(upload)
    db.session.add(upload_file)
    db.session.commit()

    resp = client.get(path.format(upload_file.id))
    assert resp.status_code == 403


def test__upload__form_study_number(client, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.collaborators.append(user)

    db.session.add(study)
    db.session.commit()

    resp = client.get("/study/{}/upload".format(study.id))

    sn = resp.soup.find("input", id="study_number")

    assert sn
    assert sn["type"] == "text"


@pytest.mark.parametrize(
    ["field_type", "input_type"],
    [
        ("BooleanField", "checkbox"),
        ("IntegerField", "text"),
        ("StringField", "text"),
        ("FileField", "file"),
    ],
)
def test__upload__form_dynamic_input(client, faker, field_type, input_type):
    add_field_types()
    user = login(client, faker)

    study = faker.study_details()
    study.collaborators.append(user)

    field = faker.field_details(field_type)
    field.study = study
    field.order = 1

    db.session.add(study)
    db.session.add(field)
    db.session.commit()

    resp = client.get("/study/{}/upload".format(study.id))

    sn = resp.soup.find(id=field.field_name)

    assert sn
    assert sn.name == "input"
    assert sn["type"] == input_type


def test__upload__form_dynamic_textarea(client, faker):
    add_field_types()
    user = login(client, faker)

    study = faker.study_details()
    study.collaborators.append(user)

    field = faker.field_details("TextAreaField")
    field.study = study
    field.order = 1

    db.session.add(study)
    db.session.add(field)
    db.session.commit()

    resp = client.get("/study/{}/upload".format(study.id))

    sn = resp.soup.find(id=field.field_name)

    assert sn
    assert sn.name == "textarea"


def test__upload__form_dynamic_radio(client, faker):
    add_field_types()
    user = login(client, faker)

    study = faker.study_details()
    study.collaborators.append(user)

    field = faker.field_details("RadioField")
    field.study = study
    field.order = 1
    field.choices = "xy|z"

    db.session.add(study)
    db.session.add(field)
    db.session.commit()

    resp = client.get("/study/{}/upload".format(study.id))

    sn = resp.soup.find(id=field.field_name)

    assert sn
    assert sn.name == "ul"
    assert sn.find("input", attrs={"type": "radio", "value": "xy"})
    assert sn.find("input", attrs={"type": "radio", "value": "z"})


def test__upload__form_dynamic_multiple(client, faker):
    add_field_types()
    user = login(client, faker)

    study = faker.study_details()
    study.collaborators.append(user)

    field1 = faker.field_details("TextAreaField")
    field1.study = study
    field1.order = 1

    field2 = faker.field_details("StringField")
    field2.study = study
    field2.order = 2

    db.session.add(study)
    db.session.add(field2)
    db.session.add(field1)
    db.session.commit()

    resp = client.get("/study/{}/upload".format(study.id))

    f1 = resp.soup.find(id=field1.field_name)

    assert f1
    assert f1.name == "textarea"

    f2 = f1.find_next(id=field2.field_name)

    assert f2
    assert f2.name == "input"
    assert f2["type"] == "text"


def _create_collaborating_study(
    user,
    faker,
    allow_duplicate_study_number=False,
    study_number_format=None,
    ):
    study = faker.study_details()
    study.collaborators.append(user)
    study.owners.append(user)
    study.allow_duplicate_study_number = allow_duplicate_study_number
    study.study_number_format = study_number_format

    db.session.add(study)
    db.session.commit()

    return study


def _do_upload(client, faker, data, study_id):
    return client.post(
        url_for("ui.upload_data", study_id=study_id),
        buffered=True,
        content_type="multipart/form-data",
        data=data,
    )


def _assert_uploaded(study_number, study, field, value):
    upload = Upload.query.filter(
        Upload.study_number == study_number and Upload.study_id == study.id
    ).first()

    assert upload

    assert UploadData.query.filter(
        UploadData.value == value
        and UploadData.field_id == field.id
        and UploadData.upload_id == upload.id
    ).first()


def _assert_uploaded_file(study_number, study, field, filename, content):
    upload = Upload.query.filter(
        Upload.study_number == study_number and Upload.study_id == study.id
    ).first()

    assert upload


    uf = UploadFile.query.filter(
        UploadFile.filename == filename
        and UploadFile.field_id == field.id
        and UploadFile.upload_id == upload.id
    ).first()

    assert uf

    saved_filepath = get_upload_filepath(uf)
    
    assert os.path.isfile(saved_filepath)

    with open(saved_filepath, 'r') as f:
        assert f.read() == content


def _assert_field_in_error(resp, field):
    e = resp.soup.find("div", class_="alert")
    assert field.field_name in e.text


def _assert_upload_not_saved(study_number):
    assert not  Upload.query.filter(
        Upload.study_number == study_number
    ).first()


def _create_Field(study, field_type, faker, required, choices="", max_length="", allowed_file_extensions=""):
    field = faker.field_details(field_type)
    field.study = study
    field.order = 1
    field.required = required
    field.choices = choices
    field.max_length = max_length
    field.allowed_file_extensions = allowed_file_extensions

    db.session.add(field)
    db.session.commit()

    return field


def _create_BooleanField(study, faker, required=False):
    return _create_Field(study, "BooleanField", faker, required)


def _create_IntegerField(study, faker, required=False):
    return _create_Field(study, "IntegerField", faker, required)


def _create_RadioField(study, faker, choices, required=False):
    return _create_Field(study, "RadioField", faker, required, choices=choices)


def _create_StringField(study, faker, max_length, required=False):
    return _create_Field(study, "StringField", faker, required, max_length=max_length)


def _create_FileField(study, faker, allowed_file_extensions, required=False):
    return _create_Field(study, "FileField", faker, required, allowed_file_extensions=allowed_file_extensions)


def test__upload__upload_study_number(client, faker):
    add_field_types()
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)

    data = {"study_number": faker.pystr(min_chars=5, max_chars=10)}

    resp = _do_upload(client, faker, data, study.id)

    assert resp.status_code == 302

    assert Upload.query.filter(
        Upload.study_number == data["study_number"] and Upload.study_id == study.id
    ).first()


def test__upload__upload_study_number__matches_format(client, faker):
    add_field_types()
    user = login(client, faker)
    study = _create_collaborating_study(user, faker, study_number_format='Tst\\d{8}[A-Z]')

    study_number = "Tst12345678X"

    data = {"study_number": study_number}

    resp = _do_upload(client, faker, data, study.id)

    assert resp.status_code == 302

    assert Upload.query.filter(
        Upload.study_number == study_number and Upload.study_id == study.id
    ).first()


def test__upload__upload_study_number__not_matches_format(client, faker):
    add_field_types()
    user = login(client, faker)
    study = _create_collaborating_study(user, faker, study_number_format='Tst\\d{8}[A-Z]')

    study_number = "Tst12345678"

    data = {"study_number": study_number}

    resp = _do_upload(client, faker, data, study.id)

    assert resp.status_code == 200

    e = resp.soup.find("div", class_="alert")
    assert 'Study Number' in e.text

    assert Upload.query.filter(
        Upload.study_number == study_number
    ).count() == 0


def test__upload__upload_study_number__duplicate_not_allowed(client, faker):
    add_field_types()
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)

    upload = faker.upload_details()
    upload.study = study

    db.session.add(upload)
    db.session.commit()

    data = {"study_number": upload.study_number}

    resp = _do_upload(client, faker, data, study.id)

    assert resp.status_code == 200

    e = resp.soup.find("div", class_="alert")
    assert 'Study Number' in e.text

    assert Upload.query.filter(
        Upload.study_number == upload.study_number
    ).count() == 1


def test__upload__upload_study_number__duplicate_allowed(client, faker):
    add_field_types()
    user = login(client, faker)
    study = _create_collaborating_study(user, faker, allow_duplicate_study_number=True)

    upload = faker.upload_details()
    upload.study = study

    db.session.add(upload)
    db.session.commit()

    data = {"study_number": upload.study_number}

    resp = _do_upload(client, faker, data, study.id)

    assert resp.status_code == 302

    assert Upload.query.filter(
        Upload.study_number == upload.study_number
    ).count() == 2


def test__upload__upload_study_number__duplicate_on_other_study(client, faker):
    add_field_types()
    user = login(client, faker)
    study1 = _create_collaborating_study(user, faker)
    study2 = _create_collaborating_study(user, faker)

    upload = faker.upload_details()
    upload.study = study1

    db.session.add(upload)
    db.session.commit()

    data = {"study_number": upload.study_number}

    resp = _do_upload(client, faker, data, study2.id)

    assert resp.status_code == 302

    assert Upload.query.filter(
        Upload.study_number == data["study_number"] and Upload.study_id == study2.id
    ).first()


@pytest.mark.parametrize(
    ["required", "value", "upload_worked", "saved_value"],
    [
        (False, "y", True, "1"),
        (False, "", True, "0"),
        (True, "y", True, "1"),
        (True, "", False, ""),
    ],
)
def test__upload__upload_BooleanField(client, faker, required, value, upload_worked, saved_value):
    add_field_types()
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)

    field = _create_BooleanField(study, faker, required)

    data = {
        "study_number": faker.pystr(min_chars=5, max_chars=10),
    }

    if value:
        data[field.field_name] = value

    resp = _do_upload(client, faker, data, study.id)

    if upload_worked:
        assert resp.status_code == 302

        _assert_uploaded(data["study_number"], study, field, value=saved_value)
    else:
        assert resp.status_code == 200

        _assert_field_in_error(resp, field)
        _assert_upload_not_saved(data["study_number"])


@pytest.mark.parametrize(
    ["required", "value", "upload_worked"],
    [
        (False, "1", True),
        (False, "q", False),
        (True, "2", True),
        (True, "", False),
    ],
)
def test__upload__upload_IntegerField(client, faker, required, value, upload_worked):
    add_field_types()
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)

    field = _create_IntegerField(study, faker, required=required)

    data = {
        "study_number": faker.pystr(min_chars=5, max_chars=10),
    }

    if value:
        data[field.field_name] = value

    resp = _do_upload(client, faker, data, study.id)

    if upload_worked:
        assert resp.status_code == 302

        _assert_uploaded(data["study_number"], study, field, value=value)
    else:
        assert resp.status_code == 200

        _assert_field_in_error(resp, field)
        _assert_upload_not_saved(data["study_number"])


@pytest.mark.parametrize(
    ["required", "value", "should_be_loaded"],
    [
        (False, "xy", True),
        (False, "q", False),
        (True, "z", True),
        (True, "", False),
    ],
)
def test__upload__upload_RadioField(client, faker, required, value, should_be_loaded):
    add_field_types()
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)

    field = _create_RadioField(study, faker, choices="xy|z", required=required)

    study_number = faker.pystr(min_chars=5, max_chars=10)

    data = {"study_number": study_number}

    if value:
        data[field.field_name] = value

    resp = _do_upload(client, faker, data, study.id)

    if should_be_loaded:
        assert resp.status_code == 302

        _assert_uploaded(data["study_number"], study, field, value=value)
    else:
        assert resp.status_code == 200

        _assert_field_in_error(resp, field)
        _assert_upload_not_saved(data["study_number"])


@pytest.mark.parametrize(
    ["required", "max_length", "value", "should_be_loaded"],
    [
        (False, 50, "x" * 50, True),
        (False, 50, "x" * 51, False),
        (True, 50, "z", True),
        (True, 50, "", False),
    ],
)
def test__upload__upload_StringField(client, faker, required, max_length, value, should_be_loaded):
    add_field_types()
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)

    field = _create_StringField(study, faker, required=required, max_length=max_length)

    study_number = faker.pystr(min_chars=5, max_chars=10)

    data = {"study_number": study_number}

    if value:
        data[field.field_name] = value

    resp = _do_upload(client, faker, data, study.id)

    if should_be_loaded:
        assert resp.status_code == 302

        _assert_uploaded(data["study_number"], study, field, value=value)
    else:
        assert resp.status_code == 200

        _assert_field_in_error(resp, field)
        _assert_upload_not_saved(data["study_number"])


@pytest.mark.parametrize(
    ["required", "allowed_file_extensions", "file_sent", "extension", "should_be_loaded"],
    [
        (False, "pdf|txt", True, "pdf", True),
        (False, "pdf|txt", True, "zip", False),
        (True, "pdf|txt", False, "", False),
        (True, "pdf|txt", True, "pdf", True),
    ],
)
def test__upload__upload_FileField(client, faker, required, allowed_file_extensions, file_sent, extension, should_be_loaded):
    add_field_types()
    user = login(client, faker)
    study = _create_collaborating_study(user, faker)

    field = _create_FileField(study, faker, required=required, allowed_file_extensions=allowed_file_extensions)

    study_number = faker.pystr(min_chars=5, max_chars=10)

    data = {"study_number": study_number}

    if file_sent:
        content = faker.text()
        filename = faker.file_name(extension=extension)

        data[field.field_name] = (
            BytesIO(content.encode('utf-8')),
            filename
        )

    resp = _do_upload(client, faker, data, study.id)

    if should_be_loaded:
        assert resp.status_code == 302

        _assert_uploaded_file(data["study_number"], study, field, filename=filename, content=content)

    else:
        assert resp.status_code == 200

        _assert_field_in_error(resp, field)
        _assert_upload_not_saved(data["study_number"])


def test__upload__delete__must_be_owner(client, faker):
    user = login(client, faker)
    user2 = faker.user_details()

    study = faker.study_details()
    study.collaborators.append(user)
    study.owners.append(user2)

    db.session.add(study)

    upload = faker.upload_details()

    upload.study = study

    db.session.add(upload)

    db.session.commit()

    resp = client.post(
        url_for("ui.upload_delete", upload_id=upload.id), data={"id": upload.id}
    )

    assert resp.status_code == 403

    changed_upload = Upload.query.get(upload.id)

    assert not changed_upload.deleted


def test__upload__delete(client, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)

    db.session.add(study)

    upload = faker.upload_details()

    upload.study = study

    db.session.add(upload)

    db.session.commit()

    resp = client.post(
        url_for("ui.upload_delete", upload_id=upload.id), data={"id": upload.id}
    )

    assert resp.status_code == 302

    changed_upload = Upload.query.get(upload.id)

    assert changed_upload.deleted


def test__upload__complete__must_be_owner(client, faker):
    user = login(client, faker)
    user2 = faker.user_details()

    study = faker.study_details()
    study.collaborators.append(user)
    study.owners.append(user2)

    db.session.add(study)

    upload = faker.upload_details()

    upload.study = study

    db.session.add(upload)

    db.session.commit()

    resp = client.post(
        url_for("ui.upload_complete", upload_id=upload.id), data={"id": upload.id}
    )

    assert resp.status_code == 403

    changed_upload = Upload.query.get(upload.id)

    assert not changed_upload.completed


def test__upload__complete(client, faker):
    user = login(client, faker)

    study = faker.study_details()
    study.owners.append(user)

    db.session.add(study)

    upload = faker.upload_details()

    upload.study = study

    db.session.add(upload)

    db.session.commit()

    resp = client.post(
        url_for("ui.upload_complete", upload_id=upload.id), data={"id": upload.id}
    )

    assert resp.status_code == 302

    changed_upload = Upload.query.get(upload.id)

    assert changed_upload.completed
