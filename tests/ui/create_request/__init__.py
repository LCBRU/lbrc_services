from flask import url_for

def _prev():
    return url_for('ui.index', _external=True)


def _url(service_id):
    return url_for('ui.create_task', service_id=service_id, prev=_prev(), _external=True)
