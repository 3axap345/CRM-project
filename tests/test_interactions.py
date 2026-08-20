from tests.helpers import create_client_record, create_interaction_record, create_user, login


def test_manager_opens_client_timeline(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        customer = create_client_record("Acme", manager.id)
        create_interaction_record("Intro call completed", customer.id, manager.id, type="call")
        customer_id = customer.id

    login(client, "manager@example.com")
    response = client.get(f"/clients/{customer_id}")

    assert response.status_code == 200
    assert b"Acme" in response.data
    assert b"Intro call completed" in response.data


def test_manager_adds_interaction_to_own_client(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        customer = create_client_record("Acme", manager.id)
        customer_id = customer.id
        manager_id = manager.id

    login(client, "manager@example.com")
    response = client.post(
        f"/clients/{customer_id}/interactions/add",
        data={"type": "email", "content": "Sent pricing details"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        from app.models.user import Interaction

        interaction = Interaction.query.filter_by(content="Sent pricing details").first()
        assert interaction is not None
        assert interaction.client_id == customer_id
        assert interaction.author_id == manager_id
        assert interaction.type == "email"


def test_manager_cannot_view_or_add_interaction_to_other_client(client, app):
    with app.app_context():
        create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        hidden_client = create_client_record("Hidden client", second.id)
        hidden_client_id = hidden_client.id

    login(client, "first@example.com")

    assert client.get(f"/clients/{hidden_client_id}").status_code == 403
    assert client.post(
        f"/clients/{hidden_client_id}/interactions/add",
        data={"type": "note", "content": "Should not work"},
    ).status_code == 403


def test_admin_can_view_all_client_interactions(client, app):
    with app.app_context():
        create_user("admin", "admin@example.com", role="admin")
        manager = create_user("manager", "manager@example.com")
        customer = create_client_record("Managed client", manager.id)
        create_interaction_record("Manager note", customer.id, manager.id)
        customer_id = customer.id

    login(client, "admin@example.com")
    response = client.get(f"/clients/{customer_id}")

    assert response.status_code == 200
    assert b"Managed client" in response.data
    assert b"Manager note" in response.data


def test_manager_deletes_own_visible_client_interaction(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        customer = create_client_record("Acme", manager.id)
        interaction = create_interaction_record("Remove me", customer.id, manager.id)
        customer_id = customer.id
        interaction_id = interaction.id

    login(client, "manager@example.com")
    response = client.post(
        f"/clients/{customer_id}/interactions/{interaction_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        from app.extensions import db
        from app.models.user import Interaction

        assert db.session.get(Interaction, interaction_id) is None


def test_manager_cannot_delete_interaction_through_other_client_url(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        first_client = create_client_record("First", manager.id)
        second_client = create_client_record("Second", manager.id)
        interaction = create_interaction_record("First note", first_client.id, manager.id)
        second_client_id = second_client.id
        interaction_id = interaction.id

    login(client, "manager@example.com")
    response = client.post(f"/clients/{second_client_id}/interactions/{interaction_id}/delete")

    assert response.status_code == 404
