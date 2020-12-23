from lbrc_flask.database import db


def get_test_request(faker, **kwargs):
    r = faker.request_details(**kwargs)

    db.session.add(r)
    db.session.commit()

    return r


def get_test_request_file(faker, **kwargs):
    r = faker.request_file_details(**kwargs)

    db.session.add(r)
    db.session.commit()

    return r


def get_test_request_type(faker, **kwargs):
    rt = faker.request_type_details(**kwargs)

    db.session.add(rt)
    db.session.commit()

    return rt


def get_test_user(faker, **kwargs):
    u = faker.user_details(**kwargs)
    db.session.add(u)

    return u
