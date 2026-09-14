from sqlalchemy import func, or_, select
from lbrc_flask.security.ldap import Ldap
from lbrc_services.model.services import Task, User
from lbrc_flask.requests import get_value_from_all_arguments
from lbrc_flask.database import db
from .. import blueprint


@blueprint.route("/user_search")
def user_search():

    q = get_value_from_all_arguments('q')
    results = []

    if q and len(q) > 1:
        users = {}

        local_users = get_local_users(q)
        ldap_users = get_ldap_users(q)

        users.update({u['id']: u for u in local_users})
        users.update({u['id']: u for u in ldap_users})

        users = sorted(users.values(), key=lambda u: (u['last_name'], u['first_name']))

        results = [{
            'id': u['id'],
            'text': u['full_name'],
        } for u in users]

    return {'results': results}


def get_ldap_users(q):
    result = []

    l = Ldap()

    if not l.is_enabled():
        return result

    l.login_nonpriv()

    for u in l.search_user(q):
        result.append({
            'id': u['username'],
            'username': u['username'],
            'full_name': '{} {} ({})'.format(
                u['given_name'],
                u['surname'],
                u['username'],
            ),
            'first_name': u['given_name'],
            'last_name': u['surname'],
        })

    return result


def get_local_users(q):
    result = []

    query = select(User).where(
            or_(
                User.username.like(f'%{q}%'),
                or_(
                    func.concat(User.first_name, ' ', User.last_name).like(f'%{q}%'),
                    User.email.like(f'%{q}%'),
                )
            )
        )

    for u in  db.session.execute(query).unique().scalars().all():
        result.append({
            'id': u.id,
            'username': u.username,
            'full_name': u.full_name,
            'first_name': u.first_name,
            'last_name': u.last_name,
        })

    return result


@blueprint.route("/task/<int:task_id>/assigned_user_options")
def task_assigned_user_options(task_id):

    task = db.get_or_404(Task, task_id)

    return {'results': [{'id': 0, 'name': 'Unassigned'}] + [{'id': o.id, 'name': o.full_name} for o in task.service.owners]}
