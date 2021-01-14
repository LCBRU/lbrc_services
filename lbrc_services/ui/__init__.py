from flask import request as flask_request, abort, jsonify
from flask_api import status
from lbrc_flask.forms import SearchForm
from lbrc_services.model import Task, TaskData, TaskFile, TaskStatus, TaskStatusType, Service, ToDo, User
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
from .decorators import must_be_task_file_owner_or_requestor, must_be_task_owner_or_requestor
from .forms import EditToDoForm, MyJobsSearchForm, TaskUpdateStatusForm, TaskSearchForm


blueprint = Blueprint("ui", __name__, template_folder="templates")


# Login required for all views
@blueprint.before_request
@login_required
def before_request():
    pass


@blueprint.route("/")
def index():
    return render_template("ui/index.html", services=Service.query.all())


@blueprint.route("/my_requests")
def my_requests():
    search_form = TaskSearchForm(formdata=flask_request.args)

    tasks = _get_tasks(search_form=search_form, requester_id=current_user.id)

    return render_template("ui/my_requests.html", tasks=tasks, search_form=search_form)


@blueprint.route("/my_jobs", methods=["GET", "POST"])
def my_jobs():

    todo_form = EditToDoForm()
    search_form = MyJobsSearchForm(formdata=flask_request.args)
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

        return redirect(url_for("ui.my_jobs", **flask_request.args))

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
    )

    if search_form.search.data:
        q = q.filter(Task.name.like("%{}%".format(search_form.search.data)))

    if search_form.data.get('service_id', 0) not in (0, "0", None):
        q = q.filter(Task.service_id == search_form.data['service_id'])

    if search_form.data.get('requestor_id', 0) not in (0, "0", None):
        q = q.filter(Task.requestor_id == search_form.data['requestor_id'])

    if 'task_status_type_id' in search_form.data:
        option = search_form.data.get('task_status_type_id', 0) or 0
        if option == 0:
            q = q.filter(Task.current_status_type_id.notin_([TaskStatusType.get_cancelled().id, TaskStatusType.get_done().id]))
        elif option == -1:
            q = q.filter(Task.current_status_type_id.in_([TaskStatusType.get_cancelled().id, TaskStatusType.get_done().id]))
        elif option != -2:
            q = q.filter(Task.current_status_type_id == option)

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


@blueprint.route("/service/<int:service_id>/create_task", methods=["GET", "POST"])
def create_task(service_id):
    service = Service.query.get_or_404(service_id)

    builder = FormBuilder()
    builder.add_form_field('name', StringField('Name', validators=[Length(max=255), DataRequired()]))
    builder.add_field_group(service.field_group)

    form = builder.get_form()

    if form.validate_on_submit():
        task = Task(service=service, requestor=current_user, name=form.name.data, current_status_type=TaskStatusType.get_created())
        task_status = TaskStatus(
            task=task,
            task_status_type=task.current_status_type,
            notes='',
        )

        db.session.add(task_status)
        db.session.add(task)

        for field_name, value in form.data.items():
            field = service.get_field_for_field_name(field_name)

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
                        db.session.add(tf)
                else:
                    db.session.add(TaskData(task=task, field=field, value=v))

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
            message='New request has been created on your before for {}'.format(
                service.name,
            ),
            recipients=[current_user.email],
        )

        return redirect(url_for("ui.index"))

    return render_template("ui/task/create.html", form=form, service=service)


@blueprint.route("/task/<int:task_id>/todo_list", methods=["GET", "POST"])
def task_todo_list(task_id):
    task = Task.query.get_or_404(task_id)
    search_form = SearchForm()
    todo_form = EditToDoForm(task_id=task_id)

    return render_template("ui/task/todo_list.html", search_form=search_form, todo_form=todo_form, task=task, prev=flask_request.args.get('prev', ''))


@blueprint.route("/todo/save", methods=["POST"])
def task_save_todo():
    form = EditToDoForm()

    if form.validate_on_submit():
        if form.todo_id.data:
            todo = ToDo.query.get_or_404(form.todo_id.data)
        else:
            todo = ToDo(task_id=form.task_id.data)
        
        todo.description = form.description.data
        db.session.add(todo)
        db.session.commit()

    return redirect(url_for("ui.task_todo_list", task_id=form.task_id.data))


@blueprint.route("/todo/update_status", methods=["POST"])
def todo_update_status():
    data = flask_request.get_json()

    todo = ToDo.query.get_or_404(data['todo_id'])

    if data['action'] == 'check':
        todo.status = 1
    elif data['action'] == 'unneeded':
        todo.status = -1
    elif data['action'] == 'uncheck':
        todo.status = 0
    
    db.session.add(todo)
    db.session.commit()

    return '', status.HTTP_205_RESET_CONTENT


@blueprint.route("/task/<int:task_id>/file/<int:task_file_id>")
@must_be_task_file_owner_or_requestor("task_file_id")
def download_task_file(task_id, task_file_id):
    t = Task.query.get_or_404(task_id)
    tf = TaskFile.query.get_or_404(task_file_id)

    return send_file(tf.local_filepath, as_attachment=True, attachment_filename=tf.filename)
