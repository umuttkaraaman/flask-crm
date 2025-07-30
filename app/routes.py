from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, and_, func
from io import StringIO
import csv

from .models import User, Client, KullaniciLog, Message
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, mail  # main blueprint'i aşağıda tanımlanacak
from .utils import admin_required, logla, generate_reset_token, verify_reset_token
from .forms import (
    RegisterForm, LoginForm, ClientForm, MessageForm, ProfileForm, PasswordChangeForm,
    RequestResetForm, ResetPasswordForm
)
from flask_mail import Message as MailMessage

main = Blueprint('main', __name__)

# Mesajlar listesi — sadece mesajlaştığın kullanıcıları göster
@main.route('/messages')
@login_required
def messages():
    sent_user_ids = db.session.query(Message.receiver_id).filter_by(sender_id=current_user.id)
    received_user_ids = db.session.query(Message.sender_id).filter_by(receiver_id=current_user.id)
    union_query = sent_user_ids.union(received_user_ids)
    user_ids = set([id for (id,) in union_query.all()])
    chatted_users = User.query.filter(User.id.in_(user_ids)).all()
    return render_template('messages.html', chatted_users=chatted_users)

# Sohbet ekranı — iki kullanıcı arasındaki mesajlar
@main.route('/messages/chat/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)
    form = MessageForm()
    form.receiver.choices = [(other_user.id, other_user.username)]

    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_user.id),
            and_(Message.sender_id == other_user.id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.timestamp.asc()).all()

    unread_msgs = Message.query.filter_by(sender_id=other_user.id, receiver_id=current_user.id, is_read=False).all()
    for msg in unread_msgs:
        msg.is_read = True
    db.session.commit()

    if form.validate_on_submit():
        new_msg = Message(
            sender_id=current_user.id,
            receiver_id=other_user.id,
            content=form.content.data
        )
        db.session.add(new_msg)
        db.session.commit()
        flash("Mesaj gönderildi!", "success")
        return redirect(url_for('main.chat', user_id=other_user.id))

    return render_template('chat.html', form=form, messages=messages, other_user=other_user)

# Yeni mesaj gönder — kullanıcı seçip mesaj atmak için (opsiyonel)
@main.route('/messages/send', methods=['GET', 'POST'])
@login_required
def send_message():
    if request.method == 'POST':
        receiver_id = request.form.get('receiver_id')
        content = request.form.get('content')

        if not content.strip():
            flash("Mesaj boş olamaz.", "warning")
            return redirect(url_for('main.send_message'))

        msg = Message(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content
        )
        db.session.add(msg)
        db.session.commit()
        flash("Mesaj gönderildi!", "success")
        return redirect(url_for('main.messages'))

    users = User.query.filter(User.id != current_user.id).all()
    return render_template("send_message.html", users=users)

# Profil sayfası
@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        existing_user_email = User.query.filter(User.email == form.email.data, User.id != current_user.id).first()
        existing_user_username = User.query.filter(User.username == form.username.data, User.id != current_user.id).first()

        if existing_user_email:
            flash("Bu e-posta başka kullanıcı tarafından kullanılıyor!", "danger")
            return redirect(url_for('main.profile'))

        if existing_user_username:
            flash("Bu kullanıcı adı zaten alınmış!", "danger")
            return redirect(url_for('main.profile'))

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Profil başarıyla güncellendi!", "success")
        return redirect(url_for('main.profile'))

    return render_template('profile.html', form=form)

# Şifre değiştirme sayfası
@main.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordChangeForm()

    if form.validate_on_submit():
        if not check_password_hash(current_user.password, form.current_password.data):
            flash("Mevcut şifreniz yanlış!", "danger")
            return redirect(url_for('main.change_password'))

        current_user.password = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash("Şifreniz başarıyla değiştirildi!", "success")
        return redirect(url_for('main.profile'))

    return render_template('change_password.html', form=form)

# Şifre sıfırlama istek sayfası
@main.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('main.reset_token', token=token, _external=True)
            msg = MailMessage("Şifre Sıfırlama Talebi", recipients=[user.email])
            msg.body = f'''Merhaba {user.username},

Şifrenizi sıfırlamak için aşağıdaki linke tıklayın:

{reset_url}

Eğer bu talebi siz göndermediyseniz lütfen dikkate almayınız.

Teşekkürler,
CRM Ekibi
'''
            mail.send(msg)
            flash('Şifre sıfırlama linki e-posta adresinize gönderildi.', 'info')
            return redirect(url_for('main.login'))
        else:
            flash('Bu e-posta adresine kayıtlı kullanıcı bulunamadı.', 'warning')
    return render_template('reset_request.html', form=form)

# Şifre sıfırlama token kontrolü ve yeni şifre belirleme
@main.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    email = verify_reset_token(token)
    if email is None:
        flash('Geçersiz veya süresi dolmuş token.', 'warning')
        return redirect(url_for('main.reset_request'))
    user = User.query.filter_by(email=email).first_or_404()
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Şifreniz başarıyla güncellendi! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('main.login'))
    return render_template('reset_token.html', form=form)

# Anasayfa
@main.route('/')
def index():
    return render_template('index.html')

# Kayıt Ol
@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Bu e-posta zaten kayıtlı!", "danger")
            return redirect(url_for('main.register'))

        hashed_pw = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        is_first_user = User.query.count() == 0
        role = 'admin' if is_first_user else 'user'

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_pw,
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Kayıt başarılı! Şimdi giriş yapabilirsiniz.", "success")
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

# Giriş
@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            logla("Giriş Yapıldı", f"{user.email} ile giriş yapıldı.")
            flash(f"Hoş geldin, {user.username}!", "success")
            return redirect(url_for('main.dashboard'))
        else:
            flash("Geçersiz e-posta ya da şifre", "danger")
    return render_template('login.html', form=form)

# Çıkış
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Çıkış yaptınız.", "info")
    return redirect(url_for('main.index'))

# Dashboard
@main.route('/dashboard')
@login_required
def dashboard():
    monthly_data = (
        db.session.query(func.month(Client.date_created), func.count(Client.id))
        .filter(Client.user_id == current_user.id)
        .group_by(func.month(Client.date_created))
        .order_by(func.month(Client.date_created))
        .all()
    )

    months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
              'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']

    counts_dict = {i: 0 for i in range(1, 13)}
    for month_num, count in monthly_data:
        counts_dict[month_num] = count

    chart_counts = list(counts_dict.values())

    return render_template('dashboard.html',
                           name=current_user.username,
                           months=months,
                           counts=chart_counts)

# Müşteri Listesi
@main.route('/clients')
@login_required
def clients():
    search = request.args.get("search")
    if search:
        clients = Client.query.filter(Client.user_id == current_user.id, Client.name.contains(search)).all()
    else:
        clients = Client.query.filter_by(user_id=current_user.id).all()
    return render_template("clients.html", clients=clients)

# Müşteri Ekle
@main.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():
    form = ClientForm()
    if form.validate_on_submit():
        new_client = Client(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            notes=form.notes.data,
            user_id=current_user.id
        )
        db.session.add(new_client)
        db.session.commit()
        logla("Müşteri Eklendi", f"{new_client.name} eklendi.")
        flash("Müşteri başarıyla eklendi!", "success")
        return redirect(url_for('main.clients'))
    return render_template("add_client.html", form=form)

# Müşteri Güncelle
@main.route('/clients/edit/<int:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if client.user_id != current_user.id:
        flash("Bu müşteriye erişim yetkiniz yok!", "danger")
        return redirect(url_for('main.clients'))

    form = ClientForm(obj=client)
    if form.validate_on_submit():
        client.name = form.name.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.notes = form.notes.data
        db.session.commit()
        logla("Müşteri Güncellendi", f"{client.name} bilgileri güncellendi.")
        flash("Müşteri bilgileri güncellendi.", "success")
        return redirect(url_for('main.clients'))

    return render_template("edit_client.html", form=form)

# Müşteri Sil
@main.route('/clients/delete/<int:client_id>')
@login_required
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    if client.user_id != current_user.id:
        flash("Bu müşteriyi silmeye yetkiniz yok!", "danger")
        return redirect(url_for('main.clients'))

    db.session.delete(client)
    db.session.commit()
    logla("Müşteri Silindi", f"{client.name} silindi.")
    flash("Müşteri silindi.", "info")
    return redirect(url_for('main.clients'))

# CSV Dışa Aktar
@main.route('/clients/export')
@login_required
def export_clients():
    clients = Client.query.filter_by(user_id=current_user.id).all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Ad', 'Email', 'Telefon', 'Not', 'Tarih'])
    for c in clients:
        writer.writerow([c.name, c.email, c.phone, c.notes, c.date_created.strftime('%Y-%m-%d')])
    output = si.getvalue()
    response = Response(output, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=musteriler.csv'
    return response

# Admin Panel
@main.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.all()
    logs = KullaniciLog.query.order_by(KullaniciLog.timestamp.desc()).limit(100).all()
    return render_template("admin_panel.html", users=users, logs=logs)
