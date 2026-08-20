from datetime import date, timedelta

from tests.helpers import (
    create_client_record,
    create_deal_record,
    create_task_record,
    create_user,
    login,
)


def test_manager_creates_task_for_own_client_and_deal(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        customer = create_client_record("Acme", manager.id)
        deal = create_deal_record("Renewal", customer.id, manager.id)
        manager_id = manager.id
        customer_id = customer.id
        deal_id = deal.id

    login(client, "manager@example.com")
    response = client.post(
        "/tasks/add",
        data={
            "title": "Call Acme",
            "description": "Discuss renewal",
            "due_date": "2026-08-25",
            "status": "todo",
            "priority": "high",
            "client_id": customer_id,
            "deal_id": deal_id,
            "assigned_to": manager_id,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        from app.models.user import Task

        task = Task.query.filter_by(title="Call Acme").first()
        assert task is not None
        assert task.client_id == customer_id
        assert task.deal_id == deal_id
        assert task.assigned_to == manager_id
        assert task.priority == "high"


def test_manager_cannot_create_task_for_other_manager_client(client, app):
    with app.app_context():
        first = create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        hidden_client = create_client_record("Hidden client", second.id)
        hidden_client_id = hidden_client.id
        first_id = first.id

    login(client, "first@example.com")
    response = client.post(
        "/tasks/add",
        data={
            "title": "Forbidden task",
            "status": "todo",
            "priority": "medium",
            "client_id": hidden_client_id,
            "deal_id": 0,
            "assigned_to": first_id,
        },
    )

    assert response.status_code == 403


def test_manager_sees_only_assigned_tasks(client, app):
    with app.app_context():
        first = create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        create_task_record("Own task", first.id)
        create_task_record("Hidden task", second.id)

    login(client, "first@example.com")
    response = client.get("/tasks/")

    assert response.status_code == 200
    assert b"Own task" in response.data
    assert b"Hidden task" not in response.data


def test_admin_sees_all_tasks(client, app):
    with app.app_context():
        admin = create_user("admin", "admin@example.com", role="admin")
        manager = create_user("manager", "manager@example.com")
        create_task_record("Admin task", admin.id)
        create_task_record("Manager task", manager.id)

    login(client, "admin@example.com")
    response = client.get("/tasks/")

    assert response.status_code == 200
    assert b"Admin task" in response.data
    assert b"Manager task" in response.data


def test_manager_cannot_edit_complete_or_delete_other_task(client, app):
    with app.app_context():
        first = create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        hidden = create_task_record("Hidden task", second.id)
        hidden_id = hidden.id

    login(client, "first@example.com")

    assert client.get(f"/tasks/edit/{hidden_id}").status_code == 403
    assert client.post(f"/tasks/complete/{hidden_id}").status_code == 403
    assert client.post(f"/tasks/delete/{hidden_id}").status_code == 403


def test_task_complete_sets_completed_at(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        task = create_task_record("Finish proposal", manager.id)
        task_id = task.id

    login(client, "manager@example.com")
    response = client.post(f"/tasks/complete/{task_id}", follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        from app.extensions import db
        from app.models.user import Task

        task = db.session.get(Task, task_id)
        assert task.status == "done"
        assert task.completed_at is not None


def test_task_overdue_and_priority_filters(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        create_task_record(
            "Overdue high task",
            manager.id,
            due_date=date.today() - timedelta(days=1),
            priority="high",
        )
        create_task_record(
            "Future low task",
            manager.id,
            due_date=date.today() + timedelta(days=1),
            priority="low",
        )

    login(client, "manager@example.com")

    overdue_response = client.get("/tasks/?overdue=1")
    assert overdue_response.status_code == 200
    assert b"Overdue high task" in overdue_response.data
    assert b"Future low task" not in overdue_response.data

    priority_response = client.get("/tasks/?priority=low")
    assert priority_response.status_code == 200
    assert b"Future low task" in priority_response.data
    assert b"Overdue high task" not in priority_response.data


def test_manager_deletes_own_task(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        task = create_task_record("Delete task", manager.id)
        task_id = task.id

    login(client, "manager@example.com")
    response = client.post(f"/tasks/delete/{task_id}", follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        from app.extensions import db
        from app.models.user import Task

        assert db.session.get(Task, task_id) is None
