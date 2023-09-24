from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired,URL

class RegisterForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),URL()])
    password = PasswordField('Password',validators=[DataRequired()])
    name = StringField('First and Last Name',validators=[DataRequired()])
    submit = SubmitField('Sign Me Up!', validators=[DataRequired()])

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), URL()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

