from wtforms import StringField, DateTimeField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class SearchForm(FlaskForm):
    source = StringField("source", validators=[DataRequired()])
    destination = StringField("destination", validators=[DataRequired()])
    departure_date = DateTimeField(
        label="departure_date", format="%Y-%m-%d", validators=[DataRequired()]
    )
