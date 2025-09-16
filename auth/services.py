from functools import wraps
from flask import request, jsonify, g
from firebase_admin import auth as firebase_auth
from core.models import Usuario

def require_auth(f):
    """Decorador para requerir autenticación con Firebase en rutas protegidas."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token no provisto'}), 401

        token = auth_header.split(' ')[1]
        try:
            decoded_token = firebase_auth.verify_id_token(token)
            uid = decoded_token['uid']
            usuario = Usuario.query.filter_by(firebase_uid=uid).first()
            if not usuario:
                return jsonify({'error': 'Usuario no registrado en base de datos'}), 403

            g.usuario_actual = usuario  # guardar usuario autenticado para usar en la vista
        except Exception as e:
            return jsonify({'error': f'Token inválido: {str(e)}'}), 401

        return f(*args, **kwargs)
    return decorated
