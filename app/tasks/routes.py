from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app import db
from app.forms import TaskForm
from app.models.user import (
    TASK_PRIORITY_CHOICES,
    TASK_STATUS_CHOICES,
    TASK_STATUS_DONE,
    Client,
    Deal,
    Task,
    User,
)

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


def visible_client_query():
    query = Client.query
    if current_user.role != "admin":
        query = query.filter_by(manager_id=current_user.id)
    return query


def visible_deal_query():
    query = Deal.query
    if current_user.role != "admin":
        query = query.filter_by(manager_id=current_user.id)
    return query


def visible_task_query():
    query = Task.query
    if current_user.role != "admin":
        query = query.filter_by(assigned_to=current_user.id)
    return query


def get_visible_task_or_404(task_id):
    task = db.get_or_404(Task, task_id)
    if current_user.role != "admin" and task.assigned_to != current_user.id:
        abort(403)
    return task


def configure_task_form(form):
    clients = visible_client_query().order_by(Client.name.asc()).all()
    deals = visible_deal_query().order_by(Deal.title.asc()).all()

    form.client_id.choices = [(0, "No client")] + [(client.id, client.name) for client in clients]
    form.deal_id.choices = [(0, "No deal")] + [(deal.id, deal.title) for deal in deals]

    if current_user.role == "admin":
        users = User.query.order_by(User.username.asc()).all()
        form.assigned_to.choices = [(user.id, user.username) for user in users]
    else:
        form.assigned_to.choices = [(current_user.id, current_user.username)]


def validate_task_links(form):
    client_id = form.client_id.data or 0
    deal_id = form.deal_id.data or 0

    client = None
    deal = None

    if client_id:
        client = visible_client_query().filter_by(id=client_id).first()
        if client is None:
            abort(403)

    if deal_id:
        deal = visible_deal_query().filter_by(id=deal_id).first()
        if deal is None:
            abort(403)
        if client is not None and deal.client_id != client.id:
            form.deal_id.errors.append("Deal must belong to the selected client.")
            return None, None, False
        if client is None:
            client = deal.client

    if current_user.role == "admin":
        assignee = db.session.get(User, form.assigned_to.data)
        if assignee is None:
            abort(404)
    elif form.assigned_to.data != current_user.id:
        abort(403)

    return client, deal, True


def reject_forbidden_task_post():
    client_id = request.form.get("client_id", type=int) or 0
    deal_id = request.form.get("deal_id", type=int) or 0
    assigned_to = request.form.get("assigned_to", type=int)

    if client_id and visible_client_query().filter_by(id=client_id).first() is None:
        abort(403)

    if deal_id and visible_deal_query().filter_by(id=deal_id).first() is None:
        abort(403)

    if current_user.role != "admin" and assigned_to != current_user.id:
        abort(403)


def apply_completed_at(task):
    if task.status == TASK_STATUS_DONE:
        if task.completed_at is None:
            task.completed_at = db.func.now()
    else:
        task.completed_at = None


@tasks_bp.route("/")
@login_required
def tasks():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    priority = request.args.get("priority", "").strip()
    overdue = request.args.get("overdue") == "1"
    query = visible_task_query()

    if search:
        query = query.outerjoin(Client).outerjoin(Deal).filter(
            or_(
                Task.title.ilike(f"%{search}%"),
                Task.description.ilike(f"%{search}%"),
                Client.name.ilike(f"%{search}%"),
                Deal.title.ilike(f"%{search}%"),
            )
        )

    if status:
        query = query.filter(Task.status == status)

    if priority:
        query = query.filter(Task.priority == priority)

    if overdue:
        query = query.filter(Task.due_date < date.today(), Task.status != TASK_STATUS_DONE)

    tasks = query.order_by(Task.due_date.is_(None), Task.due_date.asc(), Task.created_at.desc()).all()
    return render_template(
        "tasks/tasks.html",
        tasks=tasks,
        task_status_choices=TASK_STATUS_CHOICES,
        task_priority_choices=TASK_PRIORITY_CHOICES,
        today=date.today(),
    )


@tasks_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_task():
    form = TaskForm()
    configure_task_form(form)

    if request.method == "POST":
        reject_forbidden_task_post()

    if form.validate_on_submit():
        client, deal, links_valid = validate_task_links(form)
        if not links_valid:
            return render_template("tasks/add_task.html", form=form)

        task = Task(
            title=form.title.data.strip(),
            description=form.description.data.strip() or None,
            due_date=form.due_date.data,
            status=form.status.data,
            priority=form.priority.data,
            client_id=client.id if client else None,
            deal_id=deal.id if deal else None,
            assigned_to=form.assigned_to.data,
        )
        apply_completed_at(task)

        db.session.add(task)
        db.session.commit()

        flash("Task added successfully.", "success")
        return redirect(url_for("tasks.tasks"))

    return render_template("tasks/add_task.html", form=form)


@tasks_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_task(id):
    task = get_visible_task_or_404(id)
    form = TaskForm(obj=task)
    configure_task_form(form)

    if request.method == "POST":
        reject_forbidden_task_post()

    if request.method == "GET":
        form.client_id.data = task.client_id or 0
        form.deal_id.data = task.deal_id or 0

    if form.validate_on_submit():
        client, deal, links_valid = validate_task_links(form)
        if not links_valid:
            return render_template("tasks/edit_task.html", task=task, form=form)

        task.title = form.title.data.strip()
        task.description = form.description.data.strip() or None
        task.due_date = form.due_date.data
        task.status = form.status.data
        task.priority = form.priority.data
        task.client_id = client.id if client else None
        task.deal_id = deal.id if deal else None
        task.assigned_to = form.assigned_to.data
        apply_completed_at(task)

        db.session.commit()
        flash("Task updated successfully.", "success")
        return redirect(url_for("tasks.tasks"))

    return render_template("tasks/edit_task.html", task=task, form=form)


@tasks_bp.route("/complete/<int:id>", methods=["POST"])
@login_required
def complete_task(id):
    task = get_visible_task_or_404(id)
    task.status = TASK_STATUS_DONE
    apply_completed_at(task)

    db.session.commit()
    flash("Task completed.", "success")
    return redirect(url_for("tasks.tasks"))


@tasks_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_task(id):
    task = get_visible_task_or_404(id)

    db.session.delete(task)
    db.session.commit()

    flash("Task deleted.", "success")
    return redirect(url_for("tasks.tasks"))
