from flask import Blueprint
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, get_jwt_identity
)
from werkzeug.security import check_password_hash
from .models import Client, User, db

api_bp = Blueprint('api', __name__, url_prefix='/api')
api = Api(api_bp)

# Kullanıcı girişi için parser
login_parser = reqparse.RequestParser()
login_parser.add_argument('email', required=True)
login_parser.add_argument('password', required=True)

# Müşteri eklemek için parser
client_parser = reqparse.RequestParser()
client_parser.add_argument('name', required=True)
client_parser.add_argument('email')
client_parser.add_argument('phone')
client_parser.add_argument('notes')

# 🔐 Giriş endpoint'i (şifre hash kontrolü ile)
class LoginAPI(Resource):
    def post(self):
        args = login_parser.parse_args()
        user = User.query.filter_by(email=args['email']).first()
        if user and check_password_hash(user.password, args['password']):
            access_token = create_access_token(identity=user.id)
            return {"token": access_token, "user": user.username}
        return {"error": "Giriş başarısız"}, 401

# 👥 Müşteri listeleme ve ekleme
class ClientListAPI(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        clients = Client.query.filter_by(user_id=user_id).all()
        return [{
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "notes": c.notes
        } for c in clients]

    @jwt_required()
    def post(self):
        args = client_parser.parse_args()
        user_id = get_jwt_identity()
        client = Client(
            name=args['name'],
            email=args['email'],
            phone=args['phone'],
            notes=args['notes'],
            user_id=user_id
        )
        db.session.add(client)
        db.session.commit()
        return {"message": "Müşteri başarıyla eklendi!"}, 201

# Endpoint'leri ekle
api.add_resource(LoginAPI, '/api/login')
api.add_resource(ClientListAPI, '/api/clients')
