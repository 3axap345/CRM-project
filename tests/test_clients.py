from tests.helpers import create_client_record, create_user, login


def test_manager_creates_client_assigned_to_self(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        manager_id = manager.id

    login(client, "manager@example.com")
    response = client.post(
        "/clients/add",
        data={
            "name": "Acme",
            "phone": "+1 555 000",
            "email": "client@example.com",
            "status": "in_progress",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        from app.models.user import Client

        created = Client.query.filter_by(name="Acme").first()
        assert created is not None
        assert created.manager_id == manager_id
        assert created.status == "in_progress"


def test_manager_sees_only_own_clients(client, app):
    with app.app_context():
        first = create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        create_client_record("Own client", first.id)
        create_client_record("Hidden client", second.id)

    login(client, "first@example.com")
    response = client.get("/clients")

    assert response.status_code == 200
    assert b"Own client" in response.data
    assert b"Hidden client" not in response.data


def test_manager_cannot_edit_other_manager_client(client, app):
    with app.app_context():
        first = create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        hidden = create_client_record("Hidden client", second.id)
        hidden_id = hidden.id

    login(client, "first@example.com")
    response = client.get(f"/clients/edit/{hidden_id}")

    assert response.status_code == 403


def test_manager_cannot_open_admin(client, app):
    with app.app_context():
        create_user("manager", "manager@example.com")

    login(client, "manager@example.com")
    response = client.get("/admin")

    assert response.status_code == 403
