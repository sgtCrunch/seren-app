from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, Email, Length, Optional
from flask_wtf.file import FileField, FileRequired, FileAllowed




class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[InputRequired()])
    email = StringField('E-mail', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])

class UserUpdateForm(FlaskForm):
    """Form for updating user profile"""

    username = StringField('Username')
    email = StringField('E-mail', validators=[Email()])
    image = FileField(validators=[FileRequired(), FileAllowed(['png'], '.png images only!')])
    password = PasswordField('Password', validators=[InputRequired()])


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])


class CompleteQuest(FlaskForm):
    """Complete Quest form"""
    image = FileField(validators=[FileRequired(), FileAllowed(['png'], '.png images only!')])
    reflection = TextAreaField(u'Reflection', [Optional(), Length(max=500)])
