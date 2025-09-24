from datetime import datetime,timezone
import logging
from flask import Blueprint, request, jsonify
from core.models import db, Usuario
from firebase_admin import auth as firebase_auth, exceptions as firebase_exceptions
from sqlalchemy.exc import SQLAlchemyError



auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Endpoint para login de usuario usando Firebase."""
    data = request.get_json()
    id_token = data.get("token")

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_uid = decoded_token['uid']

        # Obtiene la info del usuario directamente desde Firebase
        user_record = firebase_auth.get_user(firebase_uid)

        # Verifica si está deshabilitado
        if user_record.disabled:
            return jsonify({"error": "Usuario deshabilitado"}), 403
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
                fecha_registro=datetime.now(timezone.utc),
                # Los siguientes campos quedan en NULL automáticamente:
                # telefono_pais, telefono_numero, descripcion
            )
            db.session.add(nuevo_usuario)
            db.session.commit()

            usuario = nuevo_usuario

        return jsonify({"idLocal": usuario.id, "message": "Usuario autenticado correctamente"}), 200

    except firebase_exceptions.FirebaseError as err:
        logging.error("Firebase error: %s", err)
        return jsonify({"error": "Error de autenticación con Firebase"}), 401
    except SQLAlchemyError as err:
        logging.error("Database error: %s", err)
        return jsonify({"error": "Error de base de datos"}), 500
    except Exception as err:  # Solo si es necesario, y documentado
        logging.error("Error inesperado: %s", err)
        return jsonify({"error": "Token inválido o error interno"}), 401
    