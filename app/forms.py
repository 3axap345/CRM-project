from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional


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
