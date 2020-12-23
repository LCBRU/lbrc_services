from flask import request as flask_request, abort
from lbrc_flask.forms import SearchForm
from lbrc_requests.model import Request, RequestData, RequestFile, RequestStatus, RequestStatusType, RequestType, User
from lbrc_flask.database import db
from lbrc_flask.emailing import email
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    send_file,
)
from flask_security import login_required, current_user
from lbrc_flask.forms.dynamic import FormBuilder
from wtforms import StringField
from wtforms.validators import Length, DataRequired
from sqlalchemy.orm import joinedload
from .decorators import must_be_request_file_owner_or_requestor, must_be_request_owner_or_requestor
from .forms import MyJobsSearchForm, RequestUpdateStatusForm, RequestSearchForm


blueprint = Blueprint("ui", __name__, template_folder="templates")


# Login required for all views
@blueprint.before_request
@login_required
def before_request():
    pass


@blueprint.route("/")
def index():
    return render_template("ui/index.html", request_types=RequestType.query.all())


@blueprint.route("/my_requests")
def my_requests():
    search_form = RequestSearchForm(formdata=flask_request.args)

    requests = _get_requests(search_form=search_form, requester_id=current_user.id)

    return render_template("ui/my_requests.html", requests=requests, search_form=search_form)


@blueprint.route("/my_jobs", methods=["GET", "POST"])
def my_jobs():

    search_form = MyJobsSearchForm(formdata=flask_request.args)
    request_update_status_form = RequestUpdateStatusForm()

    if request_update_status_form.validate_on_submit():
        request = Request.query.get_or_404(request_update_status_form.request_id.data)

        if not current_user in request.request_type.owners:
            abort(403)

        status_type = RequestStatusType.query.get_or_404(request_update_status_form.status.data)

        request_status = RequestStatus(
            request=request,
            request_status_type=status_type,
            notes=request_update_status_form.notes.data,
        )

        db.session.add(request_status)

        request.current_status_type = status_type

        db.session.add(request)
        db.session.commit()

        return redirect(url_for("ui.my_jobs", **flask_request.args))

    requests = _get_requests(search_form=search_form, owner_id=current_user.id, sort_asc=True)

    return render_template("ui/my_jobs.html", requests=requests, search_form=search_form, request_update_status_form=request_update_status_form)


@blueprint.route("/request/<int:request_id>/status_history")
@must_be_request_owner_or_requestor("request_id")
def request_status_history(request_id):
    request_statuses = RequestStatus.query.filter(RequestStatus.request_id == request_id).order_by(RequestStatus.created_date.desc()).all()

    return render_template("ui/_request_status_history.html", request_statuses=request_statuses)


def _get_requests(search_form, owner_id=None, requester_id=None, sort_asc=False):

    q = Request.query.options(
        joinedload(Request.data),
        joinedload(Request.files),
    )

    if search_form.search.data:
        q = q.filter(Request.name.like("%{}%".format(search_form.search.data)))

    if search_form.data.get('request_type_id', 0) not in (0, "0", None):
        q = q.filter(Request.request_type_id == search_form.data['request_type_id'])

    if search_form.data.get('requestor_id', 0) not in (0, "0", None):
        q = q.filter(Request.requestor_id == search_form.data['requestor_id'])

    if 'request_status_type_id' in search_form.data:
        option = search_form.data.get('request_status_type_id', 0) or 0
        if option == 0:
            q = q.filter(Request.current_status_type_id.notin_([RequestStatusType.get_cancelled().id, RequestStatusType.get_done().id]))
        elif option == -1:
            q = q.filter(Request.current_status_type_id.in_([RequestStatusType.get_cancelled().id, RequestStatusType.get_done().id]))
        elif option != -2:
            q = q.filter(Request.current_status_type_id == option)

    if owner_id is not None:
        q = q.join(Request.request_type)
        q = q.join(RequestType.owners)
        q = q.filter(User.id == owner_id)

    if requester_id is not None:
        q = q.filter(Request.requestor_id == requester_id)

    if sort_asc:
        q = q.order_by(Request.created_date.asc())
    else:
        q = q.order_by(Request.created_date.desc())

    return q.paginate(
            page=search_form.page.data,
            per_page=5,
            error_out=False,
        )


@blueprint.route("/request_type/<int:request_type_id>/create_request", methods=["GET", "POST"])
def create_request(request_type_id):
    request_type = RequestType.query.get_or_404(request_type_id)

    builder = FormBuilder()
    builder.add_form_field('name', StringField('Name', validators=[Length(max=255), DataRequired()]))
    builder.add_field_group(request_type.field_group)

    form = builder.get_form()

    if form.validate_on_submit():
        request = Request(request_type=request_type, requestor=current_user, name=form.name.data, current_status_type=RequestStatusType.get_created())
        request_status = RequestStatus(
            request=request,
            request_status_type=request.current_status_type,
            notes='',
        )

        db.session.add(request_status)
        db.session.add(request)

        for field_name, value in form.data.items():
            field = request_type.get_field_for_field_name(field_name)

            if not field:
                continue

            if type(value) is list:
                values = value
            else:
                values = [value]

            for v in values:

                if field.field_type.is_file:
                    if v is not None:
                        rf = RequestFile(request=request, field=field)
                        rf.set_filename_and_save(v)
                        db.session.add(rf)
                else:
                    db.session.add(RequestData(request=request, field=field, value=v))

        db.session.commit()

        email(
            subject="{} New Request".format(request_type.name),
            message="A new request has been created for {} by {}.".format(
                request_type.name,
                current_user.full_name,
            ),
            recipients=[r.email for r in request_type.owners],
        )

        email(
            subject="{} Request".format(request_type.name),
            message='New request has been created on your before for {}'.format(
                request_type.name,
            ),
            recipients=[current_user.email],
        )

        return redirect(url_for("ui.index"))

    return render_template("ui/request/create.html", form=form, request_type=request_type)


@blueprint.route("/request/<int:request_id>/file/<int:request_file_id>")
@must_be_request_file_owner_or_requestor("request_file_id")
def download_request_file(request_id, request_file_id):
    rf = RequestFile.query.get_or_404(request_file_id)

    return send_file(rf.local_filepath, as_attachment=True, attachment_filename=rf.filename)
