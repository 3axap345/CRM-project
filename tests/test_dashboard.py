from datetime import date, datetime, timedelta
from decimal import Decimal

from app.dashboard import build_dashboard_metrics
from app.extensions import db
from tests.helpers import create_client_record, create_deal_record, create_task_record, create_user, login


def test_manager_dashboard_metrics_are_scoped_to_own_records(client, app):
    today = date(2026, 8, 20)

    with app.app_context():
        first = create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        own_client = create_client_record("Own client", first.id)
        hidden_client = create_client_record("Hidden client", second.id)
        won_deal = create_deal_record("Won deal", own_client.id, first.id, amount="1500.00", status="won")
        create_deal_record("Active deal", own_client.id, first.id, amount="500.00", status="proposal")
        create_deal_record("Hidden deal", hidden_client.id, second.id, amount="9000.00", status="won")
        create_task_record("Own overdue", first.id, due_date=today - timedelta(days=1))
        create_task_record("Hidden overdue", second.id, due_date=today - timedelta(days=1))

        won_deal.closed_at = datetime(2026, 8, 20, 10, 0)
        db.session.commit()

        metrics = build_dashboard_metrics(first, today=today)

    assert metrics["total_clients"] == 1
    assert metrics["total_deals"] == 2
    assert metrics["won_deals"] == 1
    assert metrics["active_deal_amount"] == Decimal("500.00")
    assert metrics["won_deal_amount"] == Decimal("1500.00")
    assert metrics["overdue_tasks"] == 1
    assert metrics["deal_status_counts"]["won"] == 1
    assert metrics["deal_status_counts"]["proposal"] == 1
    assert metrics["revenue_values"][-1] == 1500.0


def test_admin_dashboard_metrics_include_all_records(client, app):
    today = date(2026, 8, 20)

    with app.app_context():
        admin = create_user("admin", "admin@example.com", role="admin")
        manager = create_user("manager", "manager@example.com")
        admin_client = create_client_record("Admin client", admin.id)
        manager_client = create_client_record("Manager client", manager.id)
        create_deal_record("Admin active", admin_client.id, admin.id, amount="300.00", status="new")
        won_deal = create_deal_record("Manager won", manager_client.id, manager.id, amount="700.00", status="won")
        lost_deal = create_deal_record("Manager lost", manager_client.id, manager.id, amount="200.00", status="lost")
        create_task_record("Admin overdue", admin.id, due_date=today - timedelta(days=2))
        create_task_record("Manager done", manager.id, due_date=today - timedelta(days=2), status="done")

        won_deal.closed_at = datetime(2026, 8, 19, 9, 30)
        lost_deal.closed_at = datetime(2026, 8, 19, 9, 30)
        db.session.commit()

        metrics = build_dashboard_metrics(admin, today=today)

    assert metrics["total_clients"] == 2
    assert metrics["total_deals"] == 3
    assert metrics["won_deals"] == 1
    assert metrics["lost_deals"] == 1
    assert metrics["total_tasks"] == 2
    assert metrics["overdue_tasks"] == 1
    assert metrics["active_deal_amount"] == Decimal("300.00")
    assert metrics["won_deal_amount"] == Decimal("700.00")
    assert metrics["conversion_rate"] == 33.3


def test_dashboard_page_renders_sales_metrics(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        customer = create_client_record("Acme", manager.id)
        create_deal_record("Proposal", customer.id, manager.id, amount="1200.00", status="proposal")

    login(client, "manager@example.com")
    response = client.get("/")

    assert response.status_code == 200
    assert b"Active pipeline" in response.data
    assert b"Sales funnel" in response.data
    assert b"Revenue over time" in response.data
