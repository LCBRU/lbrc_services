from lbrc_flask.security import current_user_id
from lbrc_services.model import Task, TaskAssignedUser, TaskData, TaskFile, TaskStatus, TaskStatusType, Service, Organisation, User
from lbrc_flask.database import db
from lbrc_flask.emailing import email
from flask import (
    render_template,
    redirect,
    url_for,
    send_file,
    request,
)
from flask_security import current_user
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from lbrc_flask.export import excel_download
from ..decorators import must_be_task_file_owner_or_requestor, must_be_task_owner_or_requestor, must_be_task_owner
from ..forms import MyJobsSearchForm, TaskUpdateStatusForm, TaskSearchForm, get_create_task_form, TaskUpdateAssignedUserForm
from .. import blueprint


@blueprint.route("/my_requests")
def my_requests():
    search_form = TaskSearchForm(formdata=request.args)

    q = _get_tasks_query(search_form=search_form, requester_id=current_user.id)

    tasks = q.paginate(
            page=search_form.page.data,
            per_page=5,
            error_out=False,
        )

    return render_template("ui/my_requests.html", tasks=tasks, search_form=search_form)


@blueprint.route("/my_jobs", methods=["GET", "POST"])
def my_jobs():
    search_form = MyJobsSearchForm(formdata=request.args)
    q = _get_tasks_query(search_form=search_form, owner_id=current_user.id, sort_asc=True)

    tasks = q.paginate(
            page=search_form.page.data,
            per_page=5,
            error_out=False,
        )

    return render_template(
        "ui/my_jobs.html",
        tasks=tasks,
        search_form=search_form,
        task_update_status_form=TaskUpdateStatusForm(),
        task_update_assigned_user_form=TaskUpdateAssignedUserForm(),
    )


@blueprint.route("/my_jobs/export")
def my_jobs_export():
    search_form = MyJobsSearchForm(formdata=request.args)
    q = _get_tasks_query(search_form=search_form, owner_id=current_user.id, sort_asc=True)

    # Use of dictionary instead of set to maintain order of headers
    headers = {
        'name': None,
        'organisation': None,
        'organisation description': None,
        'service': None,
        'requestor': None,
        'status': None,
        'assigned to': None,
    }

    task_details = []

    for t in q.all():
        td = {}
        task_details.append(td)

        td['name'] = t.name
        td['organisation'] = t.organisation.name
        td['organisation_description'] = t.organisation_description
        td['service'] = t.service.name
        td['requestor'] = t.requestor.full_name
        td['status'] = t.current_status_type.name

        if t.current_assigned_user:
            td['assigned to'] = t.current_assigned_user.full_name

        for d in t.data:
            headers[d.field.get_label()] = None

            td[d.field.get_label()] = d.formated_value
            
    return excel_download('My Jobs', headers.keys(), task_details)


@blueprint.route("/task/update_status", methods=["POST"])
@must_be_task_owner("task_id")
def task_update_status():
    task_update_status_form = TaskUpdateStatusForm()

    if task_update_status_form.validate_on_submit():
        task = Task.query.get_or_404(task_update_status_form.task_id.data)

        status_type = TaskStatusType.query.get_or_404(task_update_status_form.status.data)

        task_status = TaskStatus(
            task=task,
            task_status_type=status_type,
            notes=task_update_status_form.notes.data,
        )

        db.session.add(task_status)

        task.current_status_type = status_type

        db.session.add(task)
        db.session.commit()

    return redirect(url_for("ui.my_jobs", **request.args))


@blueprint.route("/task/update_assigned_user", methods=["POST"])
@must_be_task_owner("task_id")
def update_assigned_user():
    task_update_assigned_user_form = TaskUpdateAssignedUserForm()

    if task_update_assigned_user_form.validate_on_submit():
        task = Task.query.get_or_404(task_update_assigned_user_form.task_id.data)

        tau = TaskAssignedUser(
            task=task,
            user_id=task_update_assigned_user_form.assigned_user.data,
            notes=task_update_assigned_user_form.notes.data,
        )

        db.session.add(tau)

        task.current_assigned_user_id = task_update_assigned_user_form.assigned_user.data

        db.session.add(task)
        db.session.commit()

    return redirect(url_for("ui.my_jobs", **request.args))


@blueprint.route("/task/<int:task_id>/status_history")
@must_be_task_owner_or_requestor("task_id")
def task_status_history(task_id):
    task_statuses = TaskStatus.query.filter(TaskStatus.task_id == task_id).order_by(TaskStatus.created_date.desc()).all()

    return render_template("ui/_task_status_history.html", task_statuses=task_statuses)


@blueprint.route("/task/<int:task_id>/assignment_history")
@must_be_task_owner_or_requestor("task_id")
def task_assignment_history(task_id):
    task_assignments = TaskAssignedUser.query.filter(TaskAssignedUser.task_id == task_id).order_by(TaskAssignedUser.created_date.desc()).all()

    return render_template("ui/_task_assignment_history.html", task_assignments=task_assignments)


def _get_tasks_query(search_form, owner_id=None, requester_id=None, sort_asc=False):

    q = Task.query.options(
        joinedload(Task.data),
        joinedload(Task.files),
        joinedload(Task.current_status_type),
    )

    if search_form.search.data:
        q = q.filter(Task.name.like("%{}%".format(search_form.search.data)))

    if search_form.data.get('service_id', 0) not in (0, "0", None):
        q = q.filter(Task.service_id == search_form.data['service_id'])

    if search_form.data.get('organisation_id', 0) not in (0, "0", None):
        q = q.filter(Task.organisation_id == search_form.data['organisation_id'])

    if search_form.data.get('requestor_id', 0) not in (0, "0", None):
        q = q.filter(Task.requestor_id == search_form.data['requestor_id'])

    if search_form.data.get('created_date_from', None):
        q = q.filter(Task.created_date >= search_form.data['created_date_from'])

    if search_form.data.get('created_date_to', None):
        q = q.filter(Task.created_date <= search_form.data['created_date_to'])

    assigned_user_id = search_form.data.get('assigned_user_id', 0)

    if assigned_user_id == -2:
        q = q.filter(or_(
            Task.current_assigned_user_id == 0,
            Task.current_assigned_user_id == None,
            Task.current_assigned_user_id == current_user_id(),
        ))
    elif assigned_user_id == -1:
        pass
    elif assigned_user_id in (0, "0", None):
        q = q.filter(or_(
            Task.current_assigned_user_id == 0,
            Task.current_assigned_user_id == None,
        ))
    else:
        q = q.filter(Task.current_assigned_user_id == assigned_user_id)

    if 'task_status_type_id' in search_form.data:
        option = search_form.data.get('task_status_type_id', 0) or 0

        q = q.join(Task.current_status_type)

        if option == 0:
            q = q.filter(TaskStatusType.is_complete == False)
        elif option == -1:
            q = q.filter(TaskStatusType.is_complete == True)
        elif option != -2:
            q = q.filter(TaskStatusType.id == option)

    if owner_id is not None:
        q = q.join(Task.service)
        q = q.join(Service.owners)
        q = q.filter(User.id == owner_id)

    if requester_id is not None:
        q = q.filter(Task.requestor_id == requester_id)

    if sort_asc:
        q = q.order_by(Task.created_date.asc())
    else:
        q = q.order_by(Task.created_date.desc())

    return q


def save_task(task, form, context):
    task.requestor_id = form.requestor_id.data
    task.organisation_id = form.organisation_id.data
    task.organisation_description = form.organisation_description.data
    task.name = form.name.data

    task.data.clear()
    db.session.add(task)

    for field_name, value in form.data.items():
        field = task.service.get_field_for_field_name(field_name)

        if not field:
            continue

        if type(value) is list:
            values = value
        else:
            values = [value]

        for v in values:
            if field.field_type.is_file:
                if v is not None:
                    tf = TaskFile(task=task, field=field)
                    tf.set_filename_and_save(v)
                    task.files.append(tf)
            else:
                td = TaskData(task=task, field=field, value=v)
                task.data.append(td)

    task_status = TaskStatus(
        task=task,
        task_status_type=task.current_status_type,
        notes='Task {} by {}'.format(context, current_user.full_name),
    )

    db.session.add(task_status)
    db.session.commit()

    email(
        subject="{} Request {}".format(task.service.name, context),
        message="Request has been {} for {} by {}.".format(
            context,
            task.service.name,
            current_user.full_name,
        ),
        recipients=task.notification_email_addresses,
        html_template='ui/email/owner_email.html',
        context=context,
        task=task,
    )


@blueprint.route("/service/<int:service_id>/create_task", methods=["GET", "POST"])
def create_task(service_id):
    service = Service.query.get_or_404(service_id)

    form = get_create_task_form(service)

    if form.validate_on_submit():
        task = Task(
            service=service,
            current_status_type=TaskStatusType.get_created(),
        )

        save_task(task, form, 'created')

        return redirect(url_for("ui.index"))

    return render_template("ui/task/create.html", form=form, service=service, other_organisation=Organisation.get_other(), allow_requestor_selection=current_user.service_owner)


@blueprint.route("/task/<int:task_id>/edit", methods=["GET", "POST"])
@must_be_task_owner_or_requestor("task_id")
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    form = get_create_task_form(task.service, task)

    if form.validate_on_submit():

        save_task(task, form, 'updated')

        return redirect(request.args.get('prev', ''))

    return render_template("ui/task/create.html", form=form, service=task.service, other_organisation=Organisation.get_other())


@blueprint.route("/task/<int:task_id>/file/<int:task_file_id>")
@must_be_task_file_owner_or_requestor("task_file_id")
def download_task_file(task_id, task_file_id):
    t = Task.query.get_or_404(task_id)
    tf = TaskFile.query.get_or_404(task_file_id)

    return send_file(tf.local_filepath, as_attachment=True, attachment_filename=tf.filename)
