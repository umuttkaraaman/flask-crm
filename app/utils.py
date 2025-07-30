from flask import abort
from flask_login import current_user
from functools import wraps
from .models import KullaniciLog, db
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
    except:
        return None
    return email


def logla(action, detail=""):
    if current_user.is_authenticated:
        log = KullaniciLog(
            user_id=current_user.id,
            action=action,
            detail=detail
        )
        db.session.add(log)
        db.session.commit()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)  # Yetkisiz erişim
        return f(*args, **kwargs)
    return decorated_function
