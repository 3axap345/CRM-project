from app.extensions import db
from app.models.user import Client, Deal, Task, User


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


def create_deal_record(title, client_id, manager_id, amount="1000.00", status="new"):
    deal = Deal(
        title=title,
        client_id=client_id,
        manager_id=manager_id,
        amount=amount,
        status=status,
    )
    db.session.add(deal)
    db.session.commit()
    return deal


def create_task_record(title, assigned_to, client_id=None, deal_id=None, due_date=None,
                       status="todo", priority="medium"):
    task = Task(
        title=title,
        assigned_to=assigned_to,
        client_id=client_id,
        deal_id=deal_id,
        due_date=due_date,
        status=status,
        priority=priority,
    )
    db.session.add(task)
    db.session.commit()
    return task


def login(test_client, email, password="password"):
    return test_client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )
