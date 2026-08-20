from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models.user import (
    DEAL_STATUS_CHOICES,
    DEAL_STATUS_LOST,
    DEAL_STATUS_WON,
    TASK_STATUS_DONE,
    Client,
    Deal,
    Task,
)


def client_query_for_user(user):
    query = Client.query
    if user.role != "admin":
        query = query.filter_by(manager_id=user.id)
    return query


def deal_query_for_user(user):
    query = Deal.query
    if user.role != "admin":
        query = query.filter_by(manager_id=user.id)
    return query


def task_query_for_user(user):
    query = Task.query
    if user.role != "admin":
        query = query.filter_by(assigned_to=user.id)
    return query


def decimal_total(value):
    return value if value is not None else Decimal("0")


def build_dashboard_metrics(user, today=None):
    today = today or date.today()
    client_query = client_query_for_user(user)
    deal_query = deal_query_for_user(user)
    task_query = task_query_for_user(user)

    total_clients = client_query.count()
    new_count = client_query_for_user(user).filter_by(status="new").count()
    in_progress_count = client_query_for_user(user).filter_by(status="in_progress").count()
    closed_count = client_query_for_user(user).filter_by(status="closed").count()

    total_deals = deal_query.count()
    won_deals = deal_query_for_user(user).filter_by(status=DEAL_STATUS_WON).count()
    lost_deals = deal_query_for_user(user).filter_by(status=DEAL_STATUS_LOST).count()
    active_deal_amount = decimal_total(
        deal_query_for_user(user)
        .filter(Deal.status.notin_([DEAL_STATUS_WON, DEAL_STATUS_LOST]))
        .with_entities(func.sum(Deal.amount))
        .scalar()
    )
    won_deal_amount = decimal_total(
        deal_query_for_user(user)
        .filter_by(status=DEAL_STATUS_WON)
        .with_entities(func.sum(Deal.amount))
        .scalar()
    )
    conversion_rate = round((won_deals / total_deals) * 100, 1) if total_deals else 0

    total_tasks = task_query.count()
    overdue_tasks = (
        task_query_for_user(user)
        .filter(Task.due_date < today, Task.status != TASK_STATUS_DONE)
        .count()
    )

    deal_status_counts = {
        status: deal_query_for_user(user).filter_by(status=status).count()
        for status, _ in DEAL_STATUS_CHOICES
    }

    revenue_start = today - timedelta(days=29)
    revenue_rows = (
        deal_query_for_user(user)
        .filter(Deal.status == DEAL_STATUS_WON, Deal.closed_at.isnot(None))
        .filter(func.date(Deal.closed_at) >= revenue_start.isoformat())
        .with_entities(func.date(Deal.closed_at).label("closed_date"), func.sum(Deal.amount))
        .group_by(func.date(Deal.closed_at))
        .order_by(func.date(Deal.closed_at))
        .all()
    )
    revenue_by_date = {str(row[0]): float(row[1] or 0) for row in revenue_rows}

    revenue_labels = []
    revenue_values = []
    for offset in range(30):
        day = revenue_start + timedelta(days=offset)
        key = day.isoformat()
        revenue_labels.append(day.strftime("%d.%m"))
        revenue_values.append(revenue_by_date.get(key, 0))

    return {
        "total_clients": total_clients,
        "new_count": new_count,
        "in_progress_count": in_progress_count,
        "closed_count": closed_count,
        "total_deals": total_deals,
        "active_deal_amount": active_deal_amount,
        "won_deal_amount": won_deal_amount,
        "won_deals": won_deals,
        "lost_deals": lost_deals,
        "conversion_rate": conversion_rate,
        "total_tasks": total_tasks,
        "overdue_tasks": overdue_tasks,
        "deal_status_counts": deal_status_counts,
        "deal_status_labels": [label for _, label in DEAL_STATUS_CHOICES],
        "deal_status_values": [deal_status_counts[status] for status, _ in DEAL_STATUS_CHOICES],
        "revenue_labels": revenue_labels,
        "revenue_values": revenue_values,
    }
