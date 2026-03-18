from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'error': 'Missing fields'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409

    u = User(username=data['username'], email=data['email'])
    u.set_password(data['password'])
    db.session.add(u)
    db.session.commit()

    token = create_access_token(identity=str(u.id))
    return jsonify({'token': token, 'user': u.to_dict()}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    u = User.query.filter_by(email=data.get('email', '')).first()
    if not u or not u.check_password(data.get('password', '')):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = create_access_token(identity=str(u.id))
    return jsonify({'token': token, 'user': u.to_dict()})


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    u = User.query.get(int(get_jwt_identity()))
    if not u:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(u.to_dict())