from lbrc_flask.database import db


def get_test_task(faker, **kwargs):
    r = faker.task_details(**kwargs)

    db.session.add(r)
    db.session.commit()

    return r


def get_test_task_file(faker, **kwargs):
    r = faker.task_file_details(**kwargs)

    print(r)

    db.session.add(r)
    db.session.commit()

    return r


def get_test_service(faker, **kwargs):
    rt = faker.service_details(**kwargs)

    db.session.add(rt)
    db.session.commit()

    return rt


def get_test_user(faker, **kwargs):
    u = faker.user_details(**kwargs)
    db.session.add(u)

    return u
