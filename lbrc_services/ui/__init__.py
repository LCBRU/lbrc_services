from flask import request, abort, current_app
from flask_api import status
from lbrc_flask.forms import SearchForm
from lbrc_services.model import Task, TaskData, TaskFile, TaskStatus, TaskStatusType, Service, Organisation, ToDo, User
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
from sqlalchemy.orm import joinedload
from .decorators import must_be_task_file_owner_or_requestor, must_be_task_owner_or_requestor, must_be_todo_owner
from .forms import EditToDoForm, MyJobsSearchForm, TaskUpdateStatusForm, TaskSearchForm, get_create_task_form
from lbrc_flask.security.ldap import Ldap
from ldap import SCOPE_SUBTREE


blueprint = Blueprint("ui", __name__, template_folder="templates")


# Login required for all views
@blueprint.before_request
@login_required
def before_request():
    pass


@blueprint.route("/")
def index():
    return render_template("ui/index.html", services=Service.query.all())


@blueprint.route("/ldap")
def ldap():
    l = Ldap()
    l.login_nonpriv()

    result = l.search('(uid=rab63)')
    return "Result X: {}".format(result)


@blueprint.route("/my_requests")
def my_requests():
    search_form = TaskSearchForm(formdata=request.args)

    tasks = _get_tasks(search_form=search_form, requester_id=current_user.id)

    return render_template("ui/my_requests.html", tasks=tasks, search_form=search_form)


@blueprint.route("/my_jobs", methods=["GET", "POST"])
def my_jobs():
    todo_form = EditToDoForm()
    search_form = MyJobsSearchForm(formdata=request.args)
    task_update_status_form = TaskUpdateStatusForm()

    if task_update_status_form.validate_on_submit():
        task = Task.query.get_or_404(task_update_status_form.task_id.data)

        if not current_user in task.service.owners:
            abort(403)

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

    tasks = _get_tasks(search_form=search_form, owner_id=current_user.id, sort_asc=True)

    return render_template("ui/my_jobs.html", tasks=tasks, search_form=search_form, todo_form=todo_form, task_update_status_form=task_update_status_form)


@blueprint.route("/task/<int:task_id>/status_history")
@must_be_task_owner_or_requestor("task_id")
def task_status_history(task_id):
    task_statuses = TaskStatus.query.filter(TaskStatus.task_id == task_id).order_by(TaskStatus.created_date.desc()).all()

    return render_template("ui/_task_status_history.html", task_statuses=task_statuses)


def _get_tasks(search_form, owner_id=None, requester_id=None, sort_asc=False):

    q = Task.query.options(
        joinedload(Task.data),
        joinedload(Task.files),
        joinedload(Task.current_status_type),
    )

    if search_form.search.data:
        q = q.filter(Task.name.like("%{}%".format(search_form.search.data)))

    if search_form.data.get('service_id', 0) not in (0, "0", None):
        q = q.filter(Task.service_id == search_form.data['service_id'])

    if search_form.data.get('requestor_id', 0) not in (0, "0", None):
        q = q.filter(Task.requestor_id == search_form.data['requestor_id'])

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

    return q.paginate(
            page=search_form.page.data,
            per_page=5,
            error_out=False,
        )


def save_task(task, form):
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


@blueprint.route("/service/<int:service_id>/create_task", methods=["GET", "POST"])
def create_task(service_id):
    service = Service.query.get_or_404(service_id)

    form = get_create_task_form(service)

    if form.validate_on_submit():
        task = Task(
            service=service,
            current_status_type=TaskStatusType.get_created(),
        )

        save_task(task, form)

        task_status = TaskStatus(
            task=task,
            task_status_type=task.current_status_type,
            notes='Task created by {}'.format(current_user.full_name),
        )

        db.session.add(task_status)
        db.session.commit()

        email(
            subject="{} New Request".format(service.name),
            message="A new request has been created for {} by {}.".format(
                service.name,
                current_user.full_name,
            ),
            recipients=[r.email for r in service.owners],
        )

        email(
            subject="{} Request".format(service.name),
            message='New request has been created on your behalf for {}'.format(
                service.name,
            ),
            recipients=[current_user.email],
        )

        return redirect(url_for("ui.index"))

    return render_template("ui/task/create.html", form=form, service=service, other_organisation=Organisation.get_other(), allow_requestor_selection=current_user.service_owner)


@blueprint.route("/task/<int:task_id>/edit", methods=["GET", "POST"])
@must_be_task_owner_or_requestor("task_id")
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    form = get_create_task_form(task.service, task)

    if form.validate_on_submit():

        save_task(task, form)

        task_status = TaskStatus(
            task=task,
            task_status_type=task.current_status_type,
            notes='Task updated by {}'.format(current_user.full_name),
        )

        db.session.commit()

        email(
            subject="{} Request Amended".format(task.service.name),
            message="Request has been amended for {} by {}.".format(
                task.service.name,
                current_user.full_name,
            ),
            recipients=[r.email for r in task.service.owners],
        )

        email(
            subject="{} Request".format(task.service.name),
            message='Request has been amended {}'.format(
                task.service.name,
            ),
            recipients=[current_user.email],
        )

        return redirect(request.args.get('prev', ''))

    return render_template("ui/task/create.html", form=form, service=task.service, other_organisation=Organisation.get_other())


@blueprint.route("/task/<int:task_id>/todo_list", methods=["GET", "POST"])
def task_todo_list(task_id):
    task = Task.query.get_or_404(task_id)
    search_form = SearchForm(formdata=request.args)
    todo_form = EditToDoForm(task_id=task_id)

    todos = _get_todos(task=task, search_form=search_form)

    return render_template("ui/task/todo_list.html", search_form=search_form, todo_form=todo_form, task=task, todos=todos)


def _get_todos(task, search_form):

    q = ToDo.query.filter(ToDo.task_id == task.id)

    if search_form.search.data:
        q = q.filter(ToDo.description.like("%{}%".format(search_form.search.data)))

    return q.paginate(
            page=search_form.page.data,
            per_page=5,
            error_out=False,
        )


@blueprint.route("/todo/save", methods=["POST"])
@must_be_task_owner_or_requestor("task_id")
def task_save_todo():
    form = EditToDoForm()

    if form.validate_on_submit():
        if form.todo_id.data:
            todo = ToDo.query.get_or_404(form.todo_id.data)
        else:
            task = Task.query.get_or_404(form.task_id.data)
            todo = ToDo(task_id=task.id)
        
        todo.description = form.description.data
        db.session.add(todo)
        db.session.commit()

    return redirect(url_for("ui.task_todo_list", task_id=form.task_id.data))


@blueprint.route("/todo/update_status", methods=["POST"])
@must_be_todo_owner("todo_id")
def todo_update_status():
    data = request.get_json()

    todo = ToDo.query.get_or_404(data['todo_id'])

    if data['action'] == 'check':
        todo.status = 1
    elif data['action'] == 'unneeded':
        todo.status = -1
    elif data['action'] == 'uncheck':
        todo.status = 0
    else:
        return 'Action "{}" not known.'.format(data['action']), status.HTTP_400_BAD_REQUEST
    
    db.session.add(todo)
    db.session.commit()

    return '', status.HTTP_205_RESET_CONTENT


@blueprint.route("/task/<int:task_id>/file/<int:task_file_id>")
@must_be_task_file_owner_or_requestor("task_file_id")
def download_task_file(task_id, task_file_id):
    t = Task.query.get_or_404(task_id)
    tf = TaskFile.query.get_or_404(task_file_id)

    return send_file(tf.local_filepath, as_attachment=True, attachment_filename=tf.filename)
