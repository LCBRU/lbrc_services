from lbrc_flask.forms import ConfirmForm
from lbrc_services.ui.views import _get_tasks_query, send_task_export
from lbrc_services.model.services import Task, TaskAssignedUser, TaskData, TaskFile, TaskStatus, TaskStatusType, Service, Organisation, User
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
from ..decorators import must_be_task_file_owner_or_requestor, must_be_task_owner_or_requestor, must_be_task_owner
from ..forms import MyJobsSearchForm, TaskUpdateStatusForm, TaskSearchForm, get_create_task_form, TaskUpdateAssignedUserForm
from .. import blueprint
from sqlalchemy import or_, select
from lbrc_flask.security import current_user_id
from flask import current_app
from lbrc_flask.export import pdf_download


@blueprint.route("/my_requests")
def my_requests():
    search_form = TaskSearchForm(formdata=request.args)
    cancel_request_form = ConfirmForm()

    q = _get_tasks_query(search_form=search_form, requester_id=current_user.id)
    q = q.order_by(Task.created_date.desc())

    tasks = db.paginate(
        select=q,
        page=search_form.page.data,
        per_page=10,
        error_out=False,
    )

    return render_template("ui/my_requests.html", tasks=tasks, search_form=search_form, cancel_request_form=cancel_request_form)


@blueprint.route("/cancel_request", methods=["POST"])
def cancel_request():
    cancel_request_form = ConfirmForm()

    update_task_status(cancel_request_form.id.data, TaskStatusType.get_cancelled(), 'Cancelled by user')

    return redirect(request.args.get('prev', ''))


@blueprint.route("/my_jobs", methods=["GET", "POST"])
def my_jobs():
    search_form = MyJobsSearchForm(formdata=request.args)
    q = _get_tasks_query(search_form=search_form, owner_id=current_user.id)

    assigned_user_id = search_form.data.get('assigned_user_id', 0)

    if assigned_user_id == -3:
        q = q.filter(or_(
            Task.current_assigned_user_id == 0,
            Task.current_assigned_user_id == None,
            Task.current_assigned_user_id == current_user_id(),
        ))
    elif assigned_user_id == -2:
        q = q.filter(Task.current_assigned_user_id == current_user_id())
    elif assigned_user_id == -1:
        pass
    elif assigned_user_id in (0, "0", None):
        q = q.filter(or_(
            Task.current_assigned_user_id == 0,
            Task.current_assigned_user_id == None,
        ))
    else:
        q = q.filter(Task.current_assigned_user_id == assigned_user_id)

    q = q.order_by(Task.created_date.asc())

    tasks = db.paginate(
            select=q,
            page=search_form.page.data,
            per_page=10,
            error_out=False,
        )

    the_task = tasks.items[0]
    print(the_task.data)

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
    q = _get_tasks_query(search_form=search_form, owner_id=current_user.id)
    q = q.order_by(Task.created_date.asc())

    return send_task_export('My Jobs', db.session.execute(q).unique().scalars())


@blueprint.route("/task/update_status", methods=["POST"])
@must_be_task_owner("task_id")
def task_update_status():
    task_update_status_form = TaskUpdateStatusForm()

    if task_update_status_form.validate_on_submit():
        status_type = db.get_or_404(TaskStatusType, task_update_status_form.status.data)

        update_task_status(
            task_update_status_form.task_id.data,
            status_type,
            task_update_status_form.notes.data,
        )

    return redirect(request.args.get('prev', ''))


def update_task_status(task_id, new_task_status_type, notes):
        task = db.get_or_404(Task, task_id)

        task_status = TaskStatus(
            task=task,
            task_status_type=new_task_status_type,
            notes=notes,
        )

        db.session.add(task_status)

        task.current_status_type = new_task_status_type

        db.session.add(task)
        db.session.commit()


@blueprint.route("/task/update_assigned_user", methods=["POST"])
@must_be_task_owner("task_id")
def update_assigned_user():
    task_update_assigned_user_form = TaskUpdateAssignedUserForm()

    if task_update_assigned_user_form.validate_on_submit():
        _update_assigned_user(
            task_update_assigned_user_form.task_id.data,
            task_update_assigned_user_form.assigned_user.data,
            notes=task_update_assigned_user_form.notes.data,
        )

    return redirect(request.args.get('prev', ''))


@blueprint.route("/task/<int:task_id>/assign_to_me")
@must_be_task_owner("task_id")
def assign_to_me(task_id):
    _update_assigned_user(
        task_id,
        current_user_id(),
    )

    return redirect(request.args.get('prev', ''))


def _update_assigned_user(task_id, user_id, notes=''):
    task = db.get_or_404(Task, task_id)

    tau = TaskAssignedUser(
        task=task,
        user_id=user_id,
        notes=notes,
    )

    db.session.add(tau)

    task.current_assigned_user_id = user_id

    db.session.add(task)
    db.session.commit()


@blueprint.route("/task/<int:task_id>/status_history")
@must_be_task_owner_or_requestor("task_id")
def task_status_history(task_id):
    task_statuses = TaskStatus.query.filter(TaskStatus.task_id == task_id).order_by(TaskStatus.created_date.desc()).all()

    return render_template("ui/_status_history.html", statuses=task_statuses)


@blueprint.route("/task/<int:task_id>/assignment_history")
@must_be_task_owner_or_requestor("task_id")
def task_assignment_history(task_id):
    task_assignments = TaskAssignedUser.query.filter(TaskAssignedUser.task_id == task_id).order_by(TaskAssignedUser.created_date.desc()).all()

    return render_template("ui/_task_assignment_history.html", task_assignments=task_assignments)


def save_task(task, form, context):

    task.requestor_id = form.requestor_id.data
    task.organisations = list(db.session.execute(select(Organisation).where(Organisation.id.in_(form.organisations.data))).scalars())
    task.organisation_description = form.organisation_description.data
    task.name = form.name.data

    assigned_user = form.assigned_user_id.data

    current_app.logger.error(f'Assigned user is {assigned_user}')
    if assigned_user and not assigned_user == '0':
        current_app.logger.error('There is an assigned user')
        tau = TaskAssignedUser(
            task=task,
            user_id=assigned_user,
        )

        db.session.add(tau)

        task.current_assigned_user_id = assigned_user

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


@blueprint.route("/service/<int:service_id>/create_task", methods=["GET", "POST"])
def create_task(service_id):
    service = db.get_or_404(Service, service_id)

    form = get_create_task_form(service)

    if form.validate_on_submit():
        task = Task(
            service=service,
            current_status_type=TaskStatusType.get_created(),
        )

        save_task(task, form, 'created')

        if current_user not in service.owners:
            email(
                subject=f"{task.service.name} Request Created",
                message=f"Request has been created for {task.service.name} by {current_user.full_name}.",
                recipients=task.notification_email_addresses,
                html_template='ui/email/owner_email.html',
                task=task,
            )

        return redirect(url_for("ui.index"))

    return render_template(
        "ui/task/create.html",
        form=form,
        service=service,
        other_organisation=Organisation.get_other(),
        allow_requestor_selection=current_user.service_owner,
        allow_assignee_selection=current_user.service_owner,
    )


@blueprint.route("/task/<int:task_id>/edit", methods=["GET", "POST"])
@must_be_task_owner_or_requestor("task_id")
def edit_task(task_id):
    task = db.get_or_404(Task, task_id)

    form = get_create_task_form(task.service, task)

    if form.validate_on_submit():

        save_task(task, form, 'updated')

        return redirect(request.args.get('prev', ''))

    return render_template(
        "ui/task/create.html",
        form=form,
        service=task.service,
        other_organisation=Organisation.get_other(),
        allow_assignee_selection=current_user.service_owner,
    )


@blueprint.route("/task/<int:task_id>/file/<int:task_file_id>")
@must_be_task_file_owner_or_requestor("task_file_id")
def download_task_file(task_id, task_file_id):
    t = db.get_or_404(Task, task_id)
    tf =db.get_or_404(TaskFile, task_file_id)

    return send_file(
        tf.local_filepath,
        download_name=tf.filename,
        as_attachment=True,
    )


@blueprint.route("/task/<int:task_id>/pdf")
@must_be_task_owner_or_requestor("task_id")
def pdf_task(task_id):
    task : Task = db.get_or_404(Task, task_id)

    return pdf_download('ui/task/pdf.html', title=f'task_{task.service.name}_{task.name}', task=task, path='./lbrc_services/ui/templates/ui/task/')
