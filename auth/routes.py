from datetime import datetime,timezone
import logging
from flask import Blueprint, request, jsonify
from core.models import db, Usuario,Rol
from firebase_admin import auth as firebase_auth, exceptions as firebase_exceptions
from sqlalchemy.exc import SQLAlchemyError



auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Endpoint para login de usuario usando Firebase."""
    # leer JSON de forma segura (acepta application/json o raw bytes)
    json_payload = request.get_json(silent=True)
    if json_payload is not None:
        data = json_payload
    else:
        raw = request.get_data()
        if isinstance(raw, (bytes, bytearray)):
            try:
                raw = raw.decode('utf-8')
            except UnicodeDecodeError:
                raw = raw.decode('latin-1', errors='replace')
        try:
            import json as _json
            data = _json.loads(raw) if isinstance(raw, str) and raw.strip() else {}
        except Exception:
            data = {}

    id_token = data.get("token")
    if not id_token:
        logging.warning("No token en request: %s", data)
        return jsonify({"error": "token missing"}), 400

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
            role = Rol.query.filter_by(id=1).first()
            if not role:
                role = Rol(nombre='user')
                db.session.add(role)
                db.session.flush()  # asigna role.id sin commitear

            # Crear nuevo usuario con campos opcionales en NULL
            nuevo_usuario = Usuario(
                firebase_uid=firebase_uid,
                nombre=nombre,
                email=email,
                foto_perfil_url=foto_perfil,
                fecha_registro=datetime.now(timezone.utc),
                role_id=role.id,
            )
            db.session.add(nuevo_usuario)
            try:
                db.session.commit()
            except SQLAlchemyError as db_err:
                db.session.rollback()
                logging.exception("Database error creating user")
                return jsonify({"error": "Error de base de datos"}), 500

            usuario = nuevo_usuario

        return jsonify({"idLocal": usuario.id, "message": "Usuario autenticado correctamente"}), 200

    except firebase_exceptions.FirebaseError as err:
        logging.exception("Firebase error")
        return jsonify({"error": "Error de autenticación con Firebase"}), 401
    except SQLAlchemyError as err:
        logging.exception("Database error")
        return jsonify({"error": "Error de base de datos"}), 500
    except Exception as err:
        logging.exception("Error inesperado")
        return jsonify({"error": "Token inválido o error interno"}), 500
    