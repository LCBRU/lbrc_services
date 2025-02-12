from lbrc_services.model.services import Task, ToDo
from lbrc_flask.database import db
from lbrc_flask.requests import get_value_from_all_arguments
from flask import (
    render_template,
    render_template_string,
    url_for,
    request,
)
from sqlalchemy import select
from lbrc_services.ui.views import get_todo_query
from ..decorators import must_be_task_owner, must_be_todo_owner
from ..forms import EditToDoForm, TodoSearchForm
from .. import blueprint
from lbrc_flask.response import refresh_results


@blueprint.route("/task/<int:task_id>/todo/add", methods=["GET", "POST"])
@must_be_task_owner("task_id")
def todo_add(task_id):
    task = db.get_or_404(Task, task_id)

    form = EditToDoForm()

    if form.validate_on_submit():
        todo = ToDo(task_id=task.id)
        todo.description = form.description.data
        db.session.add(todo)
        db.session.commit()
        return refresh_results()

    return render_template(
        "lbrc/form_modal.html",
        title=f"Add To Do",
        form=form,
        url=url_for('ui.todo_add', task_id=task.id),
        closing_events=['refresh_results'],
    )


@blueprint.route("/todo/<int:todo_id>/edit", methods=["GET", "POST"])
@must_be_todo_owner("todo_id")
def todo_edit(todo_id):
    todo = db.get_or_404(ToDo, todo_id)

    form = EditToDoForm(obj=todo)

    if form.validate_on_submit():
        todo.description = form.description.data
        db.session.add(todo)
        db.session.commit()
        return refresh_results()

    return render_template(
        "lbrc/form_modal.html",
        title=f"Edit To Do",
        form=form,
        url=url_for('ui.todo_edit', todo_id=todo_id),
        closing_events=['refresh_results'],
    )


@blueprint.route("/todo/<int:todo_id>/set_complete", methods=["POST"])
@must_be_todo_owner("todo_id")
def todo_set_complete(todo_id):
    todo = db.get_or_404(ToDo, todo_id)

    todo.status = todo.COMPLETED_VALUE
    db.session.add(todo)
    db.session.commit()
    return todo_status_result(todo)


@blueprint.route("/todo/<int:todo_id>/set_unneeded", methods=["POST"])
@must_be_todo_owner("todo_id")
def todo_set_unneeded(todo_id):
    todo = db.get_or_404(ToDo, todo_id)

    todo.status = todo.NOT_REQUIRED_VALUE
    db.session.add(todo)
    db.session.commit()
    return todo_status_result(todo)


@blueprint.route("/todo/<int:todo_id>/set_oustanding", methods=["POST"])
@must_be_todo_owner("todo_id")
def todo_set_outstanding(todo_id):
    todo = db.get_or_404(ToDo, todo_id)

    todo.status = todo.OUTSTANDING_VALUE
    db.session.add(todo)
    db.session.commit()
    return todo_status_result(todo)


def todo_status_result(todo):
    template = '''
        {% from "ui/todo/todo_status_icon.html" import render_todo_status %}

        {{ render_todo_status(todo) }}
    '''

    return render_template_string(
        template,
        todo=todo,
    )


@blueprint.route("/task/<int:task_id>/todos")
@must_be_task_owner("task_id")
def task_todos(task_id):
    t: Task = db.get_or_404(Task, task_id)

    return render_template(
        "lbrc/search.html",
        title=f"Todos for Task '{t.name}'",
        results_url=url_for('ui.task_todos_search_results', task_id=t.id),
    )


@blueprint.route("/task/<int:task_id>/todos/search_results/<int:page>")
@blueprint.route("/task/<int:task_id>/todos/search_results")
@must_be_task_owner("task_id")
def task_todos_search_results(task_id, page=1):
    t: Task = db.get_or_404(Task, task_id)

    q = select(ToDo).where(ToDo.task_id == task_id)

    if x:= get_value_from_all_arguments('search_string') or '':
        q = q.where(ToDo.description.like(f"%{x}%"))

    return render_template(
        "ui/todo/todo_search_results.html",
        task=t,
        results=db.paginate(select=q),
    )
