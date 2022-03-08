from flask_security import roles_accepted
from lbrc_services.model import Task
from lbrc_services.ui.views import send_task_export
from .. import blueprint


@blueprint.route("/export")
@roles_accepted('exporter')
def export():
    return send_task_export('All Tasks', Task.query.all())
