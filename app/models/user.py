from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

DEAL_STATUS_NEW = "new"
DEAL_STATUS_QUALIFIED = "qualified"
DEAL_STATUS_PROPOSAL = "proposal"
DEAL_STATUS_NEGOTIATION = "negotiation"
DEAL_STATUS_WON = "won"
DEAL_STATUS_LOST = "lost"

DEAL_STATUS_CHOICES = (
    (DEAL_STATUS_NEW, "New"),
    (DEAL_STATUS_QUALIFIED, "Qualified"),
    (DEAL_STATUS_PROPOSAL, "Proposal"),
    (DEAL_STATUS_NEGOTIATION, "Negotiation"),
    (DEAL_STATUS_WON, "Won"),
    (DEAL_STATUS_LOST, "Lost"),
)
DEAL_STATUS_VALUES = tuple(value for value, _ in DEAL_STATUS_CHOICES)
CLOSED_DEAL_STATUSES = (DEAL_STATUS_WON, DEAL_STATUS_LOST)

TASK_STATUS_TODO = "todo"
TASK_STATUS_IN_PROGRESS = "in_progress"
TASK_STATUS_DONE = "done"

TASK_STATUS_CHOICES = (
    (TASK_STATUS_TODO, "To do"),
    (TASK_STATUS_IN_PROGRESS, "In progress"),
    (TASK_STATUS_DONE, "Done"),
)
TASK_STATUS_VALUES = tuple(value for value, _ in TASK_STATUS_CHOICES)

TASK_PRIORITY_LOW = "low"
TASK_PRIORITY_MEDIUM = "medium"
TASK_PRIORITY_HIGH = "high"

TASK_PRIORITY_CHOICES = (
    (TASK_PRIORITY_LOW, "Low"),
    (TASK_PRIORITY_MEDIUM, "Medium"),
    (TASK_PRIORITY_HIGH, "High"),
)
TASK_PRIORITY_VALUES = tuple(value for value, _ in TASK_PRIORITY_CHOICES)

INTERACTION_TYPE_NOTE = "note"
INTERACTION_TYPE_CALL = "call"
INTERACTION_TYPE_MEETING = "meeting"
INTERACTION_TYPE_EMAIL = "email"

INTERACTION_TYPE_CHOICES = (
    (INTERACTION_TYPE_NOTE, "Note"),
    (INTERACTION_TYPE_CALL, "Call"),
    (INTERACTION_TYPE_MEETING, "Meeting"),
    (INTERACTION_TYPE_EMAIL, "Email"),
)
INTERACTION_TYPE_VALUES = tuple(value for value, _ in INTERACTION_TYPE_CHOICES)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="manager")
    created_at = db.Column(db.DateTime, default=db.func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.username}>"


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    status = db.Column(db.String(50), default="new", nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    manager_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_client_manager"),
        nullable=True
    )

    manager = db.relationship("User", backref=db.backref("clients", lazy="dynamic"))


class Deal(db.Model):
    __tablename__ = "deals"
    __table_args__ = (
        db.CheckConstraint(
            f"status IN {DEAL_STATUS_VALUES}",
            name="ck_deals_status_valid",
        ),
        db.CheckConstraint("amount >= 0", name="ck_deals_amount_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(50), default=DEAL_STATUS_NEW, nullable=False)
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", name="fk_deal_client", ondelete="CASCADE"),
        nullable=False
    )
    manager_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_deal_manager", ondelete="CASCADE"),
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    closed_at = db.Column(db.DateTime)

    client = db.relationship(
        "Client",
        backref=db.backref("deals", lazy="dynamic", cascade="all, delete-orphan"),
    )
    manager = db.relationship("User", backref=db.backref("deals", lazy="dynamic"))


class Task(db.Model):
    __tablename__ = "tasks"
    __table_args__ = (
        db.CheckConstraint(
            f"status IN {TASK_STATUS_VALUES}",
            name="ck_tasks_status_valid",
        ),
        db.CheckConstraint(
            f"priority IN {TASK_PRIORITY_VALUES}",
            name="ck_tasks_priority_valid",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(50), default=TASK_STATUS_TODO, nullable=False)
    priority = db.Column(db.String(50), default=TASK_PRIORITY_MEDIUM, nullable=False)
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", name="fk_task_client", ondelete="CASCADE"),
        nullable=True
    )
    deal_id = db.Column(
        db.Integer,
        db.ForeignKey("deals.id", name="fk_task_deal", ondelete="SET NULL"),
        nullable=True
    )
    assigned_to = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_task_assigned_user", ondelete="CASCADE"),
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=db.func.now())
    completed_at = db.Column(db.DateTime)

    client = db.relationship(
        "Client",
        backref=db.backref("tasks", lazy="dynamic", cascade="all, delete-orphan"),
    )
    deal = db.relationship("Deal", backref=db.backref("tasks", lazy="dynamic"))
    assignee = db.relationship("User", backref=db.backref("tasks", lazy="dynamic"))


class Interaction(db.Model):
    __tablename__ = "interactions"
    __table_args__ = (
        db.CheckConstraint(
            f"type IN {INTERACTION_TYPE_VALUES}",
            name="ck_interactions_type_valid",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), default=INTERACTION_TYPE_NOTE, nullable=False)
    content = db.Column(db.Text, nullable=False)
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id", name="fk_interaction_client", ondelete="CASCADE"),
        nullable=False
    )
    author_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_interaction_author", ondelete="CASCADE"),
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=db.func.now())

    client = db.relationship(
        "Client",
        backref=db.backref("interactions", lazy="dynamic", cascade="all, delete-orphan"),
    )
    author = db.relationship("User", backref=db.backref("interactions", lazy="dynamic"))


class ClientActivity(db.Model):
    __tablename__ = "client_activity"

    id = db.Column(db.Integer, primary_key=True)
    # Исправлен FK — теперь ссылается на правильную таблицу "clients"
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"))
    action = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.now())
