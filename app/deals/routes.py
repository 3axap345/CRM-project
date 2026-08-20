from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app import db
from app.forms import DealForm
from app.models.user import CLOSED_DEAL_STATUSES, DEAL_STATUS_CHOICES, Client, Deal

deals_bp = Blueprint("deals", __name__, url_prefix="/deals")


def visible_client_query():
    query = Client.query
    if current_user.role != "admin":
        query = query.filter_by(manager_id=current_user.id)
    return query


def visible_deal_query():
    query = Deal.query.join(Client)
    if current_user.role != "admin":
        query = query.filter(Deal.manager_id == current_user.id)
    return query


def get_visible_deal_or_404(deal_id):
    deal = db.get_or_404(Deal, deal_id)
    if current_user.role != "admin" and deal.manager_id != current_user.id:
        abort(403)
    return deal


def configure_deal_form(form):
    clients = visible_client_query().order_by(Client.name.asc()).all()
    form.client_id.choices = [(client.id, client.name) for client in clients]
    return clients


def apply_closed_at(deal):
    if deal.status in CLOSED_DEAL_STATUSES:
        if deal.closed_at is None:
            deal.closed_at = db.func.now()
    else:
        deal.closed_at = None


@deals_bp.route("/")
@login_required
def deals():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    query = visible_deal_query()

    if search:
        query = query.filter(
            or_(
                Deal.title.ilike(f"%{search}%"),
                Deal.description.ilike(f"%{search}%"),
                Client.name.ilike(f"%{search}%"),
            )
        )

    if status:
        query = query.filter(Deal.status == status)

    deals = query.order_by(Deal.created_at.desc()).all()
    return render_template(
        "deals/deals.html",
        deals=deals,
        deal_status_choices=DEAL_STATUS_CHOICES,
    )


@deals_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_deal():
    form = DealForm()
    clients = configure_deal_form(form)

    if not clients:
        flash("Create a client before adding a deal.", "danger")
        return redirect(url_for("main.add_client"))

    if request.method == "POST":
        client_id = request.form.get("client_id", type=int)
        if client_id and visible_client_query().filter_by(id=client_id).first() is None:
            abort(403)

    if form.validate_on_submit():
        client = visible_client_query().filter_by(id=form.client_id.data).first()
        if client is None:
            abort(403)

        deal = Deal(
            title=form.title.data.strip(),
            description=form.description.data.strip() or None,
            amount=form.amount.data,
            status=form.status.data,
            client_id=client.id,
            manager_id=client.manager_id or current_user.id,
        )
        apply_closed_at(deal)

        db.session.add(deal)
        db.session.commit()

        flash("Deal added successfully.", "success")
        return redirect(url_for("deals.deals"))

    return render_template("deals/add_deal.html", form=form)


@deals_bp.route("/<int:id>")
@login_required
def deal_detail(id):
    deal = get_visible_deal_or_404(id)
    return render_template("deals/deal_detail.html", deal=deal)


@deals_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_deal(id):
    deal = get_visible_deal_or_404(id)
    form = DealForm(obj=deal)
    configure_deal_form(form)

    if form.validate_on_submit():
        client = visible_client_query().filter_by(id=form.client_id.data).first()
        if client is None:
            abort(403)

        deal.title = form.title.data.strip()
        deal.description = form.description.data.strip() or None
        deal.amount = form.amount.data
        deal.status = form.status.data
        deal.client_id = client.id
        if current_user.role == "admin":
            deal.manager_id = client.manager_id or current_user.id
        apply_closed_at(deal)

        db.session.commit()
        flash("Deal updated successfully.", "success")
        return redirect(url_for("deals.deal_detail", id=deal.id))

    return render_template("deals/edit_deal.html", deal=deal, form=form)


@deals_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_deal(id):
    deal = get_visible_deal_or_404(id)

    db.session.delete(deal)
    db.session.commit()

    flash("Deal deleted.", "success")
    return redirect(url_for("deals.deals"))
