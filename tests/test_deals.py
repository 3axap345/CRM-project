from tests.helpers import create_client_record, create_deal_record, create_user, login


def test_manager_creates_deal_for_own_client(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        customer = create_client_record("Acme", manager.id)
        manager_id = manager.id
        customer_id = customer.id

    login(client, "manager@example.com")
    response = client.post(
        "/deals/add",
        data={
            "title": "Support renewal",
            "description": "Annual support",
            "amount": "2500.50",
            "status": "proposal",
            "client_id": customer_id,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        from app.models.user import Deal

        deal = Deal.query.filter_by(title="Support renewal").first()
        assert deal is not None
        assert str(deal.amount) == "2500.50"
        assert deal.status == "proposal"
        assert deal.manager_id == manager_id
        assert deal.client_id == customer_id


def test_manager_cannot_create_deal_for_other_manager_client(client, app):
    with app.app_context():
        first = create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        create_client_record("Own client", first.id)
        hidden_client = create_client_record("Hidden client", second.id)
        hidden_client_id = hidden_client.id

    login(client, "first@example.com")
    response = client.post(
        "/deals/add",
        data={
            "title": "Forbidden deal",
            "amount": "100.00",
            "status": "new",
            "client_id": hidden_client_id,
        },
    )

    assert response.status_code == 403


def test_manager_sees_only_own_deals(client, app):
    with app.app_context():
        first = create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        own_client = create_client_record("Own client", first.id)
        hidden_client = create_client_record("Hidden client", second.id)
        create_deal_record("Own deal", own_client.id, first.id)
        create_deal_record("Hidden deal", hidden_client.id, second.id)

    login(client, "first@example.com")
    response = client.get("/deals/")

    assert response.status_code == 200
    assert b"Own deal" in response.data
    assert b"Hidden deal" not in response.data


def test_admin_sees_all_deals(client, app):
    with app.app_context():
        admin = create_user("admin", "admin@example.com", role="admin")
        manager = create_user("manager", "manager@example.com")
        admin_client = create_client_record("Admin client", admin.id)
        manager_client = create_client_record("Manager client", manager.id)
        create_deal_record("Admin deal", admin_client.id, admin.id)
        create_deal_record("Manager deal", manager_client.id, manager.id)

    login(client, "admin@example.com")
    response = client.get("/deals/")

    assert response.status_code == 200
    assert b"Admin deal" in response.data
    assert b"Manager deal" in response.data


def test_manager_cannot_open_or_edit_other_manager_deal(client, app):
    with app.app_context():
        create_user("first", "first@example.com")
        second = create_user("second", "second@example.com")
        hidden_client = create_client_record("Hidden client", second.id)
        hidden_deal = create_deal_record("Hidden deal", hidden_client.id, second.id)
        hidden_deal_id = hidden_deal.id

    login(client, "first@example.com")

    assert client.get(f"/deals/{hidden_deal_id}").status_code == 403
    assert client.get(f"/deals/edit/{hidden_deal_id}").status_code == 403
    assert client.post(f"/deals/delete/{hidden_deal_id}").status_code == 403


def test_deal_search_and_status_filter(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        customer = create_client_record("Acme", manager.id)
        create_deal_record("Website redesign", customer.id, manager.id, status="won")
        create_deal_record("Mobile app", customer.id, manager.id, status="lost")

    login(client, "manager@example.com")

    search_response = client.get("/deals/?search=website")
    assert search_response.status_code == 200
    assert b"Website redesign" in search_response.data
    assert b"Mobile app" not in search_response.data

    filter_response = client.get("/deals/?status=lost")
    assert filter_response.status_code == 200
    assert b"Mobile app" in filter_response.data
    assert b"Website redesign" not in filter_response.data


def test_deal_update_sets_closed_at_for_won_status(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        customer = create_client_record("Acme", manager.id)
        deal = create_deal_record("Renewal", customer.id, manager.id)
        deal_id = deal.id
        customer_id = customer.id

    login(client, "manager@example.com")
    response = client.post(
        f"/deals/edit/{deal_id}",
        data={
            "title": "Renewal",
            "description": "",
            "amount": "1200.00",
            "status": "won",
            "client_id": customer_id,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        from app.extensions import db
        from app.models.user import Deal

        deal = db.session.get(Deal, deal_id)
        assert deal is not None
        assert deal.status == "won"
        assert deal.closed_at is not None


def test_manager_deletes_own_deal(client, app):
    with app.app_context():
        manager = create_user("manager", "manager@example.com")
        customer = create_client_record("Acme", manager.id)
        deal = create_deal_record("Delete me", customer.id, manager.id)
        deal_id = deal.id

    login(client, "manager@example.com")
    response = client.post(f"/deals/delete/{deal_id}", follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        from app.extensions import db
        from app.models.user import Deal

        assert db.session.get(Deal, deal_id) is None
