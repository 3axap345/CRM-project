from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Blueprint, g, jsonify, request
from sqlalchemy import or_

from app.extensions import db
from app.models.user import (
    CLOSED_DEAL_STATUSES,
    DEAL_STATUS_VALUES,
    TASK_PRIORITY_VALUES,
    TASK_STATUS_DONE,
    TASK_STATUS_VALUES,
    Client,
    Deal,
    Task,
    User,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


def error_response(message, status_code):
    return jsonify({"error": message}), status_code


def require_api_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        auth = request.authorization
        if not auth:
            response = error_response("Authentication required", 401)
            response[0].headers["WWW-Authenticate"] = 'Basic realm="CRM API"'
            return response

        user = User.query.filter_by(email=auth.username).first()
        if user is None:
            user = User.query.filter_by(username=auth.username).first()

        if user is None or not user.check_password(auth.password):
            return error_response("Invalid credentials", 401)

        g.api_user = user
        return view(*args, **kwargs)

    return wrapped


def request_json():
    data = request.get_json(silent=True)
    if data is None:
        return None, error_response("JSON body is required", 400)
    return data, None


def visible_client_query():
    query = Client.query
    if g.api_user.role != "admin":
        query = query.filter_by(manager_id=g.api_user.id)
    return query


def visible_deal_query():
    query = Deal.query
    if g.api_user.role != "admin":
        query = query.filter_by(manager_id=g.api_user.id)
    return query


def visible_task_query():
    query = Task.query
    if g.api_user.role != "admin":
        query = query.filter_by(assigned_to=g.api_user.id)
    return query


def get_visible_client(client_id):
    client = db.session.get(Client, client_id)
    if client is None:
        return None, error_response("Client not found", 404)
    if g.api_user.role != "admin" and client.manager_id != g.api_user.id:
        return None, error_response("Forbidden", 403)
    return client, None


def get_visible_deal(deal_id):
    deal = db.session.get(Deal, deal_id)
    if deal is None:
        return None, error_response("Deal not found", 404)
    if g.api_user.role != "admin" and deal.manager_id != g.api_user.id:
        return None, error_response("Forbidden", 403)
    return deal, None


def get_visible_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        return None, error_response("Task not found", 404)
    if g.api_user.role != "admin" and task.assigned_to != g.api_user.id:
        return None, error_response("Forbidden", 403)
    return task, None


def parse_decimal(value, field_name="amount"):
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None, error_response(f"{field_name} must be a number", 400)
    if parsed < 0:
        return None, error_response(f"{field_name} must be greater than or equal to 0", 400)
    return parsed, None


def parse_date(value, field_name="due_date"):
    if value in (None, ""):
        return None, None
    try:
        return date.fromisoformat(value), None
    except (TypeError, ValueError):
        return None, error_response(f"{field_name} must be YYYY-MM-DD", 400)


def serialize_client(client):
    return {
        "id": client.id,
        "name": client.name,
        "phone": client.phone,
        "email": client.email,
        "status": client.status,
        "manager_id": client.manager_id,
        "created_at": client.created_at.isoformat() if client.created_at else None,
    }


def serialize_deal(deal):
    return {
        "id": deal.id,
        "title": deal.title,
        "description": deal.description,
        "amount": str(deal.amount),
        "status": deal.status,
        "client_id": deal.client_id,
        "manager_id": deal.manager_id,
        "created_at": deal.created_at.isoformat() if deal.created_at else None,
        "updated_at": deal.updated_at.isoformat() if deal.updated_at else None,
        "closed_at": deal.closed_at.isoformat() if deal.closed_at else None,
    }


def serialize_task(task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "status": task.status,
        "priority": task.priority,
        "client_id": task.client_id,
        "deal_id": task.deal_id,
        "assigned_to": task.assigned_to,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


def apply_closed_at(deal):
    if deal.status in CLOSED_DEAL_STATUSES:
        if deal.closed_at is None:
            deal.closed_at = db.func.now()
    else:
        deal.closed_at = None


def apply_completed_at(task):
    if task.status == TASK_STATUS_DONE:
        if task.completed_at is None:
            task.completed_at = db.func.now()
    else:
        task.completed_at = None


@api_bp.route("/clients", methods=["GET"])
@require_api_auth
def list_clients():
    search = request.args.get("search", "").strip()
    query = visible_client_query()

    if search:
        query = query.filter(Client.name.ilike(f"%{search}%"))

    clients = query.order_by(Client.created_at.desc()).all()
    return jsonify({"clients": [serialize_client(client) for client in clients]})


@api_bp.route("/clients", methods=["POST"])
@require_api_auth
def create_client():
    data, error = request_json()
    if error:
        return error

    name = str(data.get("name", "")).strip()
    if not name:
        return error_response("name is required", 400)

    client = Client(
        name=name,
        phone=data.get("phone") or None,
        email=data.get("email") or None,
        status=data.get("status") or "new",
        manager_id=g.api_user.id,
    )
    db.session.add(client)
    db.session.commit()
    return jsonify(serialize_client(client)), 201


@api_bp.route("/clients/<int:client_id>", methods=["GET"])
@require_api_auth
def get_client(client_id):
    client, error = get_visible_client(client_id)
    if error:
        return error
    return jsonify(serialize_client(client))


@api_bp.route("/clients/<int:client_id>", methods=["PUT", "PATCH"])
@require_api_auth
def update_client(client_id):
    client, error = get_visible_client(client_id)
    if error:
        return error

    data, error = request_json()
    if error:
        return error

    if "name" in data:
        name = str(data.get("name", "")).strip()
        if not name:
            return error_response("name cannot be empty", 400)
        client.name = name
    if "phone" in data:
        client.phone = data.get("phone") or None
    if "email" in data:
        client.email = data.get("email") or None
    if "status" in data:
        client.status = data.get("status") or client.status

    db.session.commit()
    return jsonify(serialize_client(client))


@api_bp.route("/clients/<int:client_id>", methods=["DELETE"])
@require_api_auth
def delete_client(client_id):
    client, error = get_visible_client(client_id)
    if error:
        return error
    if g.api_user.role != "admin":
        return error_response("Forbidden", 403)

    db.session.delete(client)
    db.session.commit()
    return "", 204


@api_bp.route("/deals", methods=["GET"])
@require_api_auth
def list_deals():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    query = visible_deal_query().join(Client)

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
    return jsonify({"deals": [serialize_deal(deal) for deal in deals]})


@api_bp.route("/deals", methods=["POST"])
@require_api_auth
def create_deal():
    data, error = request_json()
    if error:
        return error

    title = str(data.get("title", "")).strip()
    if not title:
        return error_response("title is required", 400)
    if data.get("status", "new") not in DEAL_STATUS_VALUES:
        return error_response("status is invalid", 400)

    client, error = get_visible_client(data.get("client_id"))
    if error:
        return error

    amount, error = parse_decimal(data.get("amount", "0"))
    if error:
        return error

    deal = Deal(
        title=title,
        description=data.get("description") or None,
        amount=amount,
        status=data.get("status", "new"),
        client_id=client.id,
        manager_id=client.manager_id or g.api_user.id,
    )
    apply_closed_at(deal)

    db.session.add(deal)
    db.session.commit()
    return jsonify(serialize_deal(deal)), 201


@api_bp.route("/deals/<int:deal_id>", methods=["GET"])
@require_api_auth
def get_deal(deal_id):
    deal, error = get_visible_deal(deal_id)
    if error:
        return error
    return jsonify(serialize_deal(deal))


@api_bp.route("/deals/<int:deal_id>", methods=["PUT", "PATCH"])
@require_api_auth
def update_deal(deal_id):
    deal, error = get_visible_deal(deal_id)
    if error:
        return error

    data, error = request_json()
    if error:
        return error

    if "title" in data:
        title = str(data.get("title", "")).strip()
        if not title:
            return error_response("title cannot be empty", 400)
        deal.title = title
    if "description" in data:
        deal.description = data.get("description") or None
    if "amount" in data:
        amount, error = parse_decimal(data.get("amount"))
        if error:
            return error
        deal.amount = amount
    if "status" in data:
        if data.get("status") not in DEAL_STATUS_VALUES:
            return error_response("status is invalid", 400)
        deal.status = data.get("status")
    if "client_id" in data:
        client, error = get_visible_client(data.get("client_id"))
        if error:
            return error
        deal.client_id = client.id
        if g.api_user.role == "admin":
            deal.manager_id = client.manager_id or g.api_user.id

    apply_closed_at(deal)
    db.session.commit()
    return jsonify(serialize_deal(deal))


@api_bp.route("/deals/<int:deal_id>", methods=["DELETE"])
@require_api_auth
def delete_deal(deal_id):
    deal, error = get_visible_deal(deal_id)
    if error:
        return error

    db.session.delete(deal)
    db.session.commit()
    return "", 204


@api_bp.route("/tasks", methods=["GET"])
@require_api_auth
def list_tasks():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    priority = request.args.get("priority", "").strip()
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

    tasks = query.order_by(Task.created_at.desc()).all()
    return jsonify({"tasks": [serialize_task(task) for task in tasks]})


def validate_task_payload(data):
    status = data.get("status", "todo")
    priority = data.get("priority", "medium")
    if status not in TASK_STATUS_VALUES:
        return None, None, None, error_response("status is invalid", 400)
    if priority not in TASK_PRIORITY_VALUES:
        return None, None, None, error_response("priority is invalid", 400)

    due_date, error = parse_date(data.get("due_date"))
    if error:
        return None, None, None, error

    client = None
    deal = None
    if data.get("client_id"):
        client, error = get_visible_client(data.get("client_id"))
        if error:
            return None, None, None, error

    if data.get("deal_id"):
        deal, error = get_visible_deal(data.get("deal_id"))
        if error:
            return None, None, None, error
        if client is not None and deal.client_id != client.id:
            return None, None, None, error_response("deal must belong to client", 400)
        if client is None:
            client = deal.client

    return client, deal, due_date, None


@api_bp.route("/tasks", methods=["POST"])
@require_api_auth
def create_task():
    data, error = request_json()
    if error:
        return error

    title = str(data.get("title", "")).strip()
    if not title:
        return error_response("title is required", 400)

    assigned_to = data.get("assigned_to", g.api_user.id)
    if g.api_user.role != "admin" and assigned_to != g.api_user.id:
        return error_response("Forbidden", 403)
    if db.session.get(User, assigned_to) is None:
        return error_response("Assignee not found", 404)

    client, deal, due_date, error = validate_task_payload(data)
    if error:
        return error

    task = Task(
        title=title,
        description=data.get("description") or None,
        due_date=due_date,
        status=data.get("status", "todo"),
        priority=data.get("priority", "medium"),
        client_id=client.id if client else None,
        deal_id=deal.id if deal else None,
        assigned_to=assigned_to,
    )
    apply_completed_at(task)

    db.session.add(task)
    db.session.commit()
    return jsonify(serialize_task(task)), 201


@api_bp.route("/tasks/<int:task_id>", methods=["GET"])
@require_api_auth
def get_task(task_id):
    task, error = get_visible_task(task_id)
    if error:
        return error
    return jsonify(serialize_task(task))


@api_bp.route("/tasks/<int:task_id>", methods=["PUT", "PATCH"])
@require_api_auth
def update_task(task_id):
    task, error = get_visible_task(task_id)
    if error:
        return error

    data, error = request_json()
    if error:
        return error

    if "title" in data:
        title = str(data.get("title", "")).strip()
        if not title:
            return error_response("title cannot be empty", 400)
        task.title = title
    if "description" in data:
        task.description = data.get("description") or None
    if "assigned_to" in data:
        if g.api_user.role != "admin" and data.get("assigned_to") != g.api_user.id:
            return error_response("Forbidden", 403)
        if db.session.get(User, data.get("assigned_to")) is None:
            return error_response("Assignee not found", 404)
        task.assigned_to = data.get("assigned_to")

    if any(field in data for field in ("status", "priority", "due_date", "client_id", "deal_id")):
        task_data = {
            "status": data.get("status", task.status),
            "priority": data.get("priority", task.priority),
            "due_date": data.get("due_date", task.due_date.isoformat() if task.due_date else None),
            "client_id": data.get("client_id", task.client_id),
            "deal_id": data.get("deal_id", task.deal_id),
        }
        client, deal, due_date, error = validate_task_payload(task_data)
        if error:
            return error
        task.status = task_data["status"]
        task.priority = task_data["priority"]
        task.due_date = due_date
        task.client_id = client.id if client else None
        task.deal_id = deal.id if deal else None

    apply_completed_at(task)
    db.session.commit()
    return jsonify(serialize_task(task))


@api_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@require_api_auth
def delete_task(task_id):
    task, error = get_visible_task(task_id)
    if error:
        return error

    db.session.delete(task)
    db.session.commit()
    return "", 204
