from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.dashboard import build_dashboard_metrics, client_query_for_user
from app.forms import ClientForm, InteractionForm
from app.models.user import Client, Interaction

main_bp = Blueprint("main", __name__)


def client_query_for_current_user():
    return client_query_for_user(current_user)


def get_visible_client_or_404(client_id):
    client = db.get_or_404(Client, client_id)
    if current_user.role != "admin" and client.manager_id != current_user.id:
        abort(403)
    return client


@main_bp.route("/")
@login_required
def home():
    metrics = build_dashboard_metrics(current_user)
    return render_template("dashboard.html", **metrics)


@main_bp.route("/clients")
@login_required
def clients():
    search = request.args.get("search")
    query = client_query_for_current_user()

    if search:
        query = query.filter(
            Client.name.ilike(f"%{search}%")
        )

    clients = query.order_by(Client.created_at.desc()).all()
    return render_template("clients.html", clients=clients)


@main_bp.route("/clients/add", methods=["GET", "POST"])
@login_required
def add_client():
    form = ClientForm()
    if form.validate_on_submit():
        new_client = Client(
            name=form.name.data.strip(),
            phone=form.phone.data.strip() or None,
            email=form.email.data.strip() or None,
            status=form.status.data,
            manager_id=current_user.id
        )

        db.session.add(new_client)
        db.session.commit()

        flash("Client added successfully.", "success")
        return redirect(url_for("main.clients"))

    return render_template("add_client.html", form=form)


@main_bp.route("/clients/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_client(id):
    client = get_visible_client_or_404(id)
    form = ClientForm(obj=client)

    if form.validate_on_submit():
        client.name = form.name.data.strip()
        client.phone = form.phone.data.strip() or None
        client.email = form.email.data.strip() or None
        client.status = form.status.data

        db.session.commit()
        flash("Client updated successfully.", "success")
        return redirect(url_for("main.clients"))

    return render_template("edit_client.html", client=client, form=form)


@main_bp.route("/clients/<int:id>")
@login_required
def client_detail(id):
    client = get_visible_client_or_404(id)
    interaction_form = InteractionForm()
    interactions = client.interactions.order_by(Interaction.created_at.desc()).all()

    return render_template(
        "client_detail.html",
        client=client,
        interaction_form=interaction_form,
        interactions=interactions,
    )


@main_bp.route("/clients/<int:id>/interactions/add", methods=["POST"])
@login_required
def add_interaction(id):
    client = get_visible_client_or_404(id)
    form = InteractionForm()

    if form.validate_on_submit():
        interaction = Interaction(
            type=form.type.data,
            content=form.content.data.strip(),
            client_id=client.id,
            author_id=current_user.id,
        )
        db.session.add(interaction)
        db.session.commit()
        flash("Interaction added.", "success")
    else:
        flash("Interaction content is required.", "danger")

    return redirect(url_for("main.client_detail", id=client.id))


@main_bp.route("/clients/<int:client_id>/interactions/<int:interaction_id>/delete", methods=["POST"])
@login_required
def delete_interaction(client_id, interaction_id):
    client = get_visible_client_or_404(client_id)
    interaction = db.get_or_404(Interaction, interaction_id)
    if interaction.client_id != client.id:
        abort(404)

    db.session.delete(interaction)
    db.session.commit()
    flash("Interaction deleted.", "success")
    return redirect(url_for("main.client_detail", id=client.id))


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

    from sqlalchemy import func

    from app.models.user import User

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
