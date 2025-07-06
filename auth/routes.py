from flask import Blueprint, request, jsonify
from core.models import db, Usuario
from firebase_admin import auth as firebase_auth
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    id_token = data.get("token")

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_uid = decoded_token['uid']
        email = decoded_token.get('email')
        nombre = decoded_token.get('name', '')
        foto_perfil = decoded_token.get('picture', '')

        # Verificar si el usuario ya existe en la base de datos
        usuario = Usuario.query.filter_by(firebase_uid=firebase_uid).first()

        if not usuario:
            # Crear nuevo usuario con campos opcionales en NULL
            nuevo_usuario = Usuario(
                firebase_uid=firebase_uid,
                nombre=nombre,
                email=email,
                foto_perfil_url=foto_perfil,
                fecha_registro=datetime.utcnow(),
                # Los siguientes campos quedan en NULL automáticamente:
                # telefono_pais, telefono_numero, descripcion
            )
            db.session.add(nuevo_usuario)
            db.session.commit()

        return jsonify({"message": "Usuario autenticado correctamente"}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Token inválido o error interno"}), 401