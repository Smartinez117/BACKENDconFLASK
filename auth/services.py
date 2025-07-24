
from functools import wraps
from flask import request, jsonify
from firebase_admin import auth as firebase_auth
from core.models import Usuario

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Falta el token de autenticación'}), 401

        token = auth_header.replace('Bearer ', '')

        try:
            decoded_token = firebase_auth.verify_id_token(token)
            firebase_uid = decoded_token['uid']
            usuario = Usuario.query.filter_by(firebase_uid=firebase_uid).first()

            if not usuario:
                return jsonify({'error': 'Usuario no registrado en la base de datos'}), 403

            return f(usuario, *args, **kwargs)  # inyecta el usuario como primer parámetro

        except Exception as e:
            print("Error de autenticación:", e)
            import traceback; traceback.print_exc()
            return jsonify({'error': 'Token inválido o expirado'}), 401

    return decorated_function