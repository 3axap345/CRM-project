from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models.user import Client
from datetime import datetime

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def home():
    total_clients = Client.query.count()

    # Исправлено: считаем реальные значения по статусу
    new_count = Client.query.filter_by(status="new").count()
    in_progress_count = Client.query.filter_by(status="in_progress").count()
    closed_count = Client.query.filter_by(status="closed").count()

    return render_template(
        "dashboard.html",
        total_clients=total_clients,
        new_count=new_count,
        in_progress_count=in_progress_count,
        closed_count=closed_count
    )


@main_bp.route("/clients")
@login_required
def clients():
    search = request.args.get("search")

    if search:
        clients = Client.query.filter(
            Client.name.ilike(f"%{search}%")
        ).all()
    else:
        clients = Client.query.all()

    return render_template("clients.html", clients=clients)


@main_bp.route("/clients/add", methods=["GET", "POST"])
@login_required
def add_client():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        status = request.form.get("status", "new")

        if not name:
            flash("Client name is required.", "danger")
            return render_template("add_client.html")

        new_client = Client(
            name=name,
            phone=phone or None,
            email=email or None,
            status=status,
            # Исправлено: привязываем менеджера при создании
            manager_id=current_user.id
        )

        db.session.add(new_client)
        db.session.commit()

        flash("Client added successfully.", "success")
        return redirect(url_for("main.clients"))

    return render_template("add_client.html")


@main_bp.route("/clients/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_client(id):
    # Исправлено: используем db.get_or_404 вместо устаревшего query.get_or_404
    client = db.get_or_404(Client, id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Client name is required.", "danger")
            return render_template("edit_client.html", client=client)

        client.name = name
        client.phone = request.form.get("phone", "").strip() or None
        client.email = request.form.get("email", "").strip() or None
        client.status = request.form.get("status", client.status)

        db.session.commit()
        flash("Client updated successfully.", "success")
        return redirect(url_for("main.clients"))

    return render_template("edit_client.html", client=client)


# Исправлено: удаление только через POST, а не GET
@main_bp.route("/clients/delete/<int:id>", methods=["POST"])
@login_required
def delete_client(id):
    if current_user.role != "admin":
        abort(403)

    client = db.get_or_404(Client, id)

    db.session.delete(client)
    db.session.commit()

    flash("Client deleted.", "success")
    return redirect(url_for("main.clients"))


# ── ADMIN ──────────────────────────────────────────────────────────────────

@main_bp.route("/admin")
@login_required
def admin():
    if current_user.role != "admin":
        abort(403)

    from app.models.user import User
    from sqlalchemy import func

    users = User.query.order_by(User.created_at.desc()).all()

    # Статистика клиентов по менеджерам
    manager_stats = (
        db.session.query(User, func.count(Client.id).label("total"))
        .outerjoin(Client, Client.manager_id == User.id)
        .group_by(User.id)
        .all()
    )

    return render_template("admin.html", users=users, manager_stats=manager_stats)


@main_bp.route("/admin/users/<int:id>/role", methods=["POST"])
@login_required
def change_role(id):
    if current_user.role != "admin":
        abort(403)

    from app.models.user import User
    user = db.get_or_404(User, id)

    if user.id == current_user.id:
        flash("Cannot change your own role.", "danger")
        return redirect(url_for("main.admin"))

    new_role = request.form.get("role")
    if new_role in ("admin", "manager"):
        user.role = new_role
        db.session.commit()
        flash(f"Роль пользователя {user.username} changed to '{new_role}'.", "success")

    return redirect(url_for("main.admin"))


@main_bp.route("/admin/users/<int:id>/delete", methods=["POST"])
@login_required
def delete_user(id):
    if current_user.role != "admin":
        abort(403)

    from app.models.user import User
    user = db.get_or_404(User, id)

    if user.id == current_user.id:
        flash("Cannot delete yourself.", "danger")
        return redirect(url_for("main.admin"))

    db.session.delete(user)
    db.session.commit()
    flash(f"Пользователь {user.username} deleted.", "success")
    return redirect(url_for("main.admin"))
