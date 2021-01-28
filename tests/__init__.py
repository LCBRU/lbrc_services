from lbrc_flask.database import db
from lbrc_flask.pytest.asserts import get_and_assert_standards
from flask import url_for


def lbrc_services_get(client, url, user, has_form=False):
    resp = get_and_assert_standards(client, url, user, has_form)

    assert resp.soup.nav is not None
    assert resp.soup.nav.find("a", href=url_for('ui.my_requests'), string="My Requests") is not None

    if user.service_owner:
        assert resp.soup.nav.find("a", href=url_for('ui.my_jobs'), string='My Jobs') is not None

    return resp


def get_test_owned_task(faker, owner, **kwargs):
    s = get_test_service(faker, owners=[owner])

    r = faker.task_details(**kwargs, service=s)

    db.session.add(r)
    db.session.commit()

    return r


def get_test_task(faker, **kwargs):
    r = faker.task_details(**kwargs)

    db.session.add(r)
    db.session.commit()

    return r


def get_test_task_file(faker, **kwargs):
    r = faker.task_file_details(**kwargs)

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
    db.session.commit()

    return u


def get_test_todo(faker, **kwargs):
    t = faker.todo_details(**kwargs)
    db.session.add(t)
    db.session.commit()

    return t
