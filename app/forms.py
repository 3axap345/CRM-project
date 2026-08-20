from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional

from app.models.user import DEAL_STATUS_CHOICES


class ClientForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=50)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    status = SelectField(
        "Status",
        choices=[
            ("new", "New"),
            ("in_progress", "In progress"),
            ("closed", "Closed"),
        ],
        default="new",
    )
    submit = SubmitField("Save")


class DealForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    amount = DecimalField(
        "Amount",
        places=2,
        validators=[DataRequired(), NumberRange(min=0)],
    )
    status = SelectField("Status", choices=list(DEAL_STATUS_CHOICES), default="new")
    client_id = SelectField("Client", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Save")
