from lbrc_services.model.services import Service
from flask import (
    Blueprint,
    render_template,
)
from flask_security import login_required
from sqlalchemy import select
from lbrc_flask.database import db


blueprint = Blueprint("ui", __name__, template_folder="templates")


# Login required for all views
@blueprint.before_request
@login_required
def before_request():
    pass


@blueprint.route("/")
def index():
    return render_template("ui/index.html", services=db.session.execute(select(Service)).scalars().all())

from .views import *
