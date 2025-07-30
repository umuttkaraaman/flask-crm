from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from wtforms import TextAreaField

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Şifre Sıfırlama Linki Gönder')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Yeni Şifre', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Yeni Şifre Tekrar', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Şifreyi Yenile')


class ProfileForm(FlaskForm):
    username = StringField("Kullanıcı Adı", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Profili Güncelle")

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField("Mevcut Şifre", validators=[DataRequired()])
    new_password = PasswordField("Yeni Şifre", validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField("Yeni Şifre Tekrar", validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField("Şifreyi Değiştir")



class RegisterForm(FlaskForm):
    username = StringField("Kullanıcı Adı", validators=[DataRequired(), Length(min=3)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Şifre", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Şifre Tekrar", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Kayıt Ol")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Şifre", validators=[DataRequired()])
    submit = SubmitField("Giriş Yap")

class ClientForm(FlaskForm):
    name = StringField("İsim", validators=[DataRequired()])
    email = StringField("Email")
    phone = StringField("Telefon")
    notes = StringField("Notlar")
    submit = SubmitField("Kaydet")


class MessageForm:
    pass