from lbrc_flask.security.ldap import Ldap
from lbrc_services.model import Task
from lbrc_flask.requests import get_value_from_all_arguments
from .. import blueprint


@blueprint.route("/user_search")
def user_search():

    q = get_value_from_all_arguments('q')
    results = []

    if q and len(q) > 1:
        l = Ldap()
        l.login_nonpriv()

        users = sorted(l.search_user(q), key=lambda u: (u['surname'], u['given_name']))

        for u in users:
            results.append({
                'id': u['username'],
                'text': '{} {} ({})'.format(
                    u['given_name'],
                    u['surname'],
                    u['username'],
                ),

            })

    return {'results': results}


@blueprint.route("/task/<int:task_id>/assigned_user_options")
def task_assigned_user_options(task_id):

    task = Task.query.get_or_404(task_id)

    return {'results': [{'id': 0, 'name': 'Unassigned'}] + [{'id': o.id, 'name': o.full_name} for o in task.service.owners]}
