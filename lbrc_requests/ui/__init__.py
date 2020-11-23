from flask import (
    Blueprint,
    render_template,
)

from flask_security import login_required


blueprint = Blueprint("ui", __name__, template_folder="templates")


# Login required for all views
@blueprint.before_request
@login_required
def before_request():
    pass


@blueprint.route("/")
def index():
    return render_template("ui/index.html")
