from bs4 import BeautifulSoup
from upload.database import db
from upload.model import FieldType


def login(client, faker):
    s = faker.site_details()
    u = faker.user_details()
    u.site = s
    db.session.add(s)
    db.session.add(u)
    db.session.commit()

    resp = client.get("/login")
    soup = BeautifulSoup(resp.data, "html.parser")

    crf_token = soup.find(
        "input", {"name": "csrf_token"}, type="hidden", id="csrf_token"
    )

    data = dict(email=u.email, password=u.password)

    if crf_token:
        data["csrf_token"] = crf_token.get("value")

    client.post("/login", data=data, follow_redirects=True)

    return u


def add_content_for_all_areas(faker, user):
    study = faker.study_details()
    study.owners.append(user)
    study.collaborators.append(user)

    db.session.add(study)

    upload = faker.upload_details()
    upload.completed = False
    upload.study = study
    upload.uploader = user

    db.session.add(upload)

    db.session.commit()

    return (study, upload)


def add_field_types():
    for t in [
        "BooleanField",
        "IntegerField",
        "RadioField",
        "StringField",
        "TextAreaField",
    ]:
        ft = FieldType(name=t)
        db.session.add(ft)

    db.session.add(FieldType(name="FileField", is_file=True))

    db.session.commit()
