import base64

from tests.helpers import create_client_record, create_deal_record, create_task_record, create_user


def auth_header(identifier, password="password"):
    token = base64.b64encode(f"{identifier}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_api_requires_authentication(client):
    response = client.get("/api/clients")

    assert response.status_code == 401
    assert response.json["error"] == "Authentication required"


def test_api_rejects_invalid_credentials(client, app):
    with app.app_context():
        create_user("manager", "manager@example.com")

    response = client.get("/api/clients", headers=auth_header("manager@example.com", "wrong"))

    assert response.status_code == 401
    assert response.json["error"] == "Invalid credentials"


def test_api_manager_lists_only_own_clients(client, app):
    with app.app_context():
        first = create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        create_client_record("Own client", first.id)
        create_client_record("Hidden client", second.id)

    response = client.get("/api/clients", headers=auth_header("first@example.com"))

    assert response.status_code == 200
    names = [item["name"] for item in response.json["clients"]]
    assert names == ["Own client"]


def test_api_client_crud_and_delete_permission(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        create_user("admin", "admin@example.com", role="admin")
        manager_id = manager.id

    create_response = client.post(
        "/api/clients",
        json={"name": "Acme", "phone": "+1 555", "status": "new"},
        headers=auth_header("manager@example.com"),
    )
    assert create_response.status_code == 201
    client_id = create_response.json["id"]
    assert create_response.json["manager_id"] == manager_id

    update_response = client.patch(
        f"/api/clients/{client_id}",
        json={"name": "Acme Corp"},
        headers=auth_header("manager@example.com"),
    )
    assert update_response.status_code == 200
    assert update_response.json["name"] == "Acme Corp"

    forbidden_delete = client.delete(
        f"/api/clients/{client_id}",
        headers=auth_header("manager@example.com"),
    )
    assert forbidden_delete.status_code == 403

    admin_delete = client.delete(
        f"/api/clients/{client_id}",
        headers=auth_header("admin@example.com"),
    )
    assert admin_delete.status_code == 204


def test_api_manager_cannot_get_other_client(client, app):
    with app.app_context():
        first = create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        hidden = create_client_record("Hidden client", second.id)
        hidden_id = hidden.id

    response = client.get(f"/api/clients/{hidden_id}", headers=auth_header("first@example.com"))

    assert response.status_code == 403


def test_api_deal_crud_and_permissions(client, app):
    with app.app_context():
        first = create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        own_client = create_client_record("Own client", first.id)
        hidden_client = create_client_record("Hidden client", second.id)
        own_client_id = own_client.id
        hidden_client_id = hidden_client.id

    forbidden_create = client.post(
        "/api/deals",
        json={"title": "Forbidden", "client_id": hidden_client_id, "amount": "100"},
        headers=auth_header("first@example.com"),
    )
    assert forbidden_create.status_code == 403

    create_response = client.post(
        "/api/deals",
        json={"title": "Renewal", "client_id": own_client_id, "amount": "1200.00", "status": "proposal"},
        headers=auth_header("first@example.com"),
    )
    assert create_response.status_code == 201
    deal_id = create_response.json["id"]
    assert create_response.json["amount"] == "1200.00"

    update_response = client.patch(
        f"/api/deals/{deal_id}",
        json={"status": "won"},
        headers=auth_header("first@example.com"),
    )
    assert update_response.status_code == 200
    assert update_response.json["status"] == "won"
    assert update_response.json["closed_at"] is not None

    hidden_get = client.get(f"/api/deals/{deal_id}", headers=auth_header("second@example.com"))
    assert hidden_get.status_code == 403

    delete_response = client.delete(f"/api/deals/{deal_id}", headers=auth_header("first@example.com"))
    assert delete_response.status_code == 204


def test_api_deal_validation(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        customer = create_client_record("Acme", manager.id)
        customer_id = customer.id

    response = client.post(
        "/api/deals",
        json={"title": "Bad deal", "client_id": customer_id, "amount": "-1"},
        headers=auth_header("manager@example.com"),
    )

    assert response.status_code == 400
    assert response.json["error"] == "amount must be greater than or equal to 0"


def test_api_task_crud_filters_and_permissions(client, app):
    with app.app_context():
        first = create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        own_client = create_client_record("Own client", first.id)
        hidden_client = create_client_record("Hidden client", second.id)
        own_deal = create_deal_record("Own deal", own_client.id, first.id)
        hidden_task = create_task_record("Hidden task", second.id, client_id=hidden_client.id)
        own_client_id = own_client.id
        own_deal_id = own_deal.id
        hidden_task_id = hidden_task.id
        second_id = second.id

    create_response = client.post(
        "/api/tasks",
        json={
            "title": "Follow up",
            "client_id": own_client_id,
            "deal_id": own_deal_id,
            "due_date": "2026-08-25",
            "priority": "high",
        },
        headers=auth_header("first@example.com"),
    )
    assert create_response.status_code == 201
    task_id = create_response.json["id"]
    assert create_response.json["assigned_to"] != second_id

    list_response = client.get("/api/tasks?priority=high", headers=auth_header("first@example.com"))
    assert list_response.status_code == 200
    assert [task["title"] for task in list_response.json["tasks"]] == ["Follow up"]

    complete_response = client.patch(
        f"/api/tasks/{task_id}",
        json={"status": "done"},
        headers=auth_header("first@example.com"),
    )
    assert complete_response.status_code == 200
    assert complete_response.json["completed_at"] is not None

    hidden_response = client.get(f"/api/tasks/{hidden_task_id}", headers=auth_header("first@example.com"))
    assert hidden_response.status_code == 403

    delete_response = client.delete(f"/api/tasks/{task_id}", headers=auth_header("first@example.com"))
    assert delete_response.status_code == 204


def test_api_manager_cannot_assign_task_to_another_user(client, app):
    with app.app_context():
        first = create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        second_id = second.id

    response = client.post(
        "/api/tasks",
        json={"title": "Bad assignment", "assigned_to": second_id},
        headers=auth_header("first@example.com"),
    )

    assert response.status_code == 403
