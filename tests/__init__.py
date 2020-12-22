from lbrc_flask.database import db


def _get_test_request_type(faker):
    rt = faker.request_type_details()

    db.session.add(rt)
    db.session.commit()

    return rt


def _get_test_user(faker):
    u = faker.user_details()
    db.session.add(u)

    return u
