from sqlalchemy import func, or_
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
        l = Ldap()
        l.login_nonpriv()

        users = {}

        if db.session.dialect.name == 'sqlite':
            query = User.query.filter(
                or_(
                    User.username.like(f'%{q}%'),
                    or_(
                        User.first_name.like(f'%{q}%'),
                        or_(
                            User.last_name.like(f'%{q}%'),
                            User.email.like(f'%{q}%'),
                        )
                    )
                )
            )
        elif db.session.dialect.name == 'mysql':
            query = User.query.filter(
                or_(
                    User.username.like(f'%{q}%'),
                    or_(
                        func.concat(User.first_name, ' ', User.last_name).like(f'%{q}%'),
                        User.email.like(f'%{q}%'),
                    )
                )
            )

        for u in query.all():
            users[u.username] = {
                'id': u.id,
                'username': u.username,
                'full_name': u.full_name,
                'first_name': u.first_name,
                'last_name': u.last_name,
            }

        for u in l.search_user(q):
            if u['username'] not in users:
                users[u['username']] = {
                    'id': u['username'],
                    'username': u['username'],
                    'full_name': '{} {} ({})'.format(
                        u['given_name'],
                        u['surname'],
                        u['username'],
                    ),
                    'first_name': u['given_name'],
                    'last_name': u['surname'],
                }

        users = sorted(users.values(), key=lambda u: (u['last_name'], u['first_name']))

        results = [{
            'id': u['id'],
            'text': u['full_name'],
        } for u in users]

    return {'results': results}


@blueprint.route("/task/<int:task_id>/assigned_user_options")
def task_assigned_user_options(task_id):

    task = db.get_or_404(Task, task_id)

    return {'results': [{'id': 0, 'name': 'Unassigned'}] + [{'id': o.id, 'name': o.full_name} for o in task.service.owners]}
