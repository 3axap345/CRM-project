from app.extensions import db
from app.models.user import Client, User


def create_user(username, email, password="password", role="manager"):
    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def create_client_record(name, manager_id, status="new"):
    client = Client(name=name, manager_id=manager_id, status=status)
    db.session.add(client)
    db.session.commit()
    return client


def login(test_client, email, password="password"):
    return test_client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )
