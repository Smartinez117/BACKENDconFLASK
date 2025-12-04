import firebase_admin
from firebase_admin import auth as firebase_auth
from flask import request, jsonify
from functools import wraps


# --------------------------------------------------------
# Función interna para obtener el header "Authorization"
# sin importar el nombre exacto o mayúsculas
# --------------------------------------------------------
def _get_auth_header():
    return (
        request.headers.get("Authorization")
        or request.headers.get("authorization")
        or request.headers.get("HTTP_AUTHORIZATION")
        or request.headers.get("X-Authorization")
        or None
    )


# --------------------------------------------------------
# Middleware require_auth
# --------------------------------------------------------
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = _get_auth_header()

        if not auth_header:
            return jsonify({"error": "Falta el token"}), 401

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Formato de token inválido"}), 401

        token = auth_header.split(" ")[1]

        try:
            decoded_token = firebase_auth.verify_id_token(token)
            request.user = decoded_token
            return f(*args, **kwargs)

        except Exception as e:
            print("Error verificando token:", e)
            return jsonify({"error": "Token inválido"}), 401

    return decorated


# --------------------------------------------------------
# Middleware require_admin
# --------------------------------------------------------
def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = _get_auth_header()

        if not auth_header:
            return jsonify({"error": "Falta el token"}), 401

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Formato de token inválido"}), 401

        token = auth_header.split(" ")[1]

        try:
            decoded_token = firebase_auth.verify_id_token(token)

            is_admin = decoded_token.get("admin", False)

            if not is_admin:
                return jsonify({"error": "No autorizado"}), 403

            request.user = decoded_token
            return f(*args, **kwargs)

        except Exception as e:
            print("Error verificando token admin:", e)
            return jsonify({"error": "Token inválido"}), 401

    return decorated
