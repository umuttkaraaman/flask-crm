from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'sır-gibi-bir-anahtar'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/flask_crm?unix_socket=/tmp/mysql.sock'
    app.config['JWT_SECRET_KEY'] = 'jwt-gizli-anahtar'

    # Flask-Mail ayarları (kendi e-posta bilgilerini gir)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'seninemail@gmail.com'      # Buraya kendi mailini yaz
    app.config['MAIL_PASSWORD'] = 'email_sifren'              # Gmail uygulama şifresi olmalı
    app.config['MAIL_DEFAULT_SENDER'] = 'seninemail@gmail.com'  # Genelde mail adresinle aynı olur

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    jwt = JWTManager(app)
    Migrate(app, db)

    from .models import User  # 🔥 Burada olmalı

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprintleri ekle
    from .routes import main
    from .api import api_bp
    app.register_blueprint(main)
    app.register_blueprint(api_bp)

    return app
