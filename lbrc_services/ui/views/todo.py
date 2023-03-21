from flask_api import status
from lbrc_flask.forms import SearchForm
from lbrc_services.model.services import Task, ToDo
from lbrc_flask.database import db
from lbrc_flask.requests import get_value_from_all_arguments
from flask import (
    render_template,
    redirect,
    url_for,
    request,
)
from ..decorators import must_be_task_owner_or_requestor, must_be_todo_owner
from ..forms import EditToDoForm
from .. import blueprint


@blueprint.route("/task/<int:task_id>/todo_list", methods=["GET", "POST"])
def task_todo_list(task_id):
    task = db.get_or_404(Task, task_id)
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
            todo = db.get_or_404(ToDo, form.todo_id.data)
        else:
            task = db.get_or_404(Task, form.task_id.data)
            todo = ToDo(task_id=task.id)
        
        todo.description = form.description.data
        db.session.add(todo)
        db.session.commit()

    return redirect(url_for("ui.task_todo_list", task_id=form.task_id.data, prev=get_value_from_all_arguments('prev')))


@blueprint.route("/todo/update_status", methods=["POST"])
@must_be_todo_owner("todo_id")
def todo_update_status():
    data = request.get_json()

    todo = db.get_or_404(ToDo, data['todo_id'])

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
