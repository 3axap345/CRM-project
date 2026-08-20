from app.models.user import User
from tests.helpers import create_user


def test_register_creates_user(client, app):
    response = client.post(
        "/register",
        data={
            "username": "manager",
            "email": "manager@example.com",
            "password": "password",
            "confirm_password": "password",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    with app.app_context():
        assert User.query.filter_by(email="manager@example.com").first() is not None


def test_login_rejects_wrong_password(client, app):
    with app.app_context():
        create_user("manager", "manager@example.com")

    response = client.post(
        "/login",
        data={"email": "manager@example.com", "password": "wrong"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Invalid credentials" in response.data
