from flask import render_template
from wtforms import StringField
from lbrc_services.model.services import Service
from lbrc_flask.database import db

from lbrc_services.ui.forms import get_create_task_form
from .. import blueprint
from lbrc_flask.export import pdf_download


@blueprint.route("/service/<int:service_id>/pdf")
def service_form_pdf(service_id):
    service : Service = db.get_or_404(Service, service_id)
    form = get_create_task_form(service, is_pdf=True)

    return pdf_download('ui/service/form_pdf.html', title=f'service_{service.name}_form', service=service, form=form, path='./lbrc_services/ui/templates/ui/service/')
    # return render_template('ui/service/form_pdf.html', title=f'service_{service.name}_form', service=service, form=form, path='./lbrc_services/ui/templates/ui/service/')
