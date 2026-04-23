from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    phone = StringField('Номер телефона', validators=[DataRequired(), Length(min=10, max=20)])
    full_name = StringField('ФИО', validators=[DataRequired(), Length(min=3, max=100)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_phone(self, phone):
        # Здесь мы не можем использовать User.query, т.к. номер будет нормализован в обработчике
        pass

class LoginForm(FlaskForm):
    phone = StringField('Номер телефона', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class SMSVerificationForm(FlaskForm):
    code = StringField('Код из SMS', validators=[DataRequired(), Length(min=4, max=6)])
    submit = SubmitField('Подтвердить')

class AddSubmissionForm(FlaskForm):
    user_id = SelectField('Пользователь', coerce=int, validators=[DataRequired()])
    material_key = SelectField('Тип вторсырья', validators=[DataRequired()])
    weight_kg = FloatField('Вес (кг)', validators=[DataRequired()])
    submit = SubmitField('Добавить сдачу')