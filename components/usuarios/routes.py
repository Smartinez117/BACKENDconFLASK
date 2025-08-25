from flask import Blueprint, request, jsonify
from core.models import db, Usuario
from components.usuarios.services import actualizar_datos_usuario , get_usuario,filtrar_usuarios_service, obtener_usuario_por_uid
from firebase_admin import auth
from auth.services import require_auth
usuarios_bp = Blueprint('usuarios', __name__)

#Endpoint para actualizar información del usuario
@usuarios_bp.route('/usuario/<int:id_usuario>', methods=['PATCH'])
def actualizar_usuario(id_usuario):
    data = request.get_json()
    try:
     actualizar_datos_usuario(id_usuario,data)
     return jsonify({'mensaje': 'Usuario actualizado con éxito'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

#Endpoint para obtener usuarios por su id
@usuarios_bp.route('/usuario/<int:id_usuario>', methods = ['GET'])
def obtener_usuario_por_id(id_usuario):
   usuario = get_usuario(id_usuario) 
   return jsonify(usuario), 200

#Endpoint para poder banear usuarios
@usuarios_bp.route('/api/<int:id_usuario>/ban', methods=['PATCH'])
@require_auth
def banear_usuario(id_usuario):

    usuario = Usuario.query.get_or_404(id_usuario)

    if usuario.rol == "admin":
        return jsonify({"error": "No se puede banear a otro administrador"}), 403

    try:
        # Deshabilitar el usuario en Firebase
        auth.update_user(usuario.firebase_uid, disabled=True)
        usuario.rol = "baneado"
        db.session.commit()

        return jsonify({"mensaje": f"Usuario {usuario.nombre} baneado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": f"No se pudo banear al usuario: {str(e)}"}), 500

#Endpoint para desbanear usuarios
@usuarios_bp.route('/api/<int:id_usuario>/desban', methods=['PATCH'])
@require_auth
def desbanear_usuario(id_usuario):
    # Buscar usuario en tu base de datos
    usuario = Usuario.query.get_or_404(id_usuario)

    # Si ya es admin, no debería estar baneado pero controlamos igual
    if usuario.rol == "admin":
        return jsonify({"error": "Los administradores no pueden ser baneados/desbaneados"}), 403

    try:
        # Rehabilitar al usuario en Firebase
        auth.update_user(usuario.firebase_uid, disabled=False)

        # Actualizar el rol en tu DB local
        usuario.rol = "usuario"
        db.session.commit()

        return jsonify({"mensaje": f"Usuario {usuario.nombre} desbaneado correctamente"}), 200
    
    except Exception as e:
        return jsonify({"error": f"No se pudo desbanear al usuario: {str(e)}"}), 500

#Endpoint para filtrar usuarios por mail, nombre , telefono y rol
@usuarios_bp.route('/api/usuarios', methods=['GET'])
def filtrar_usuarios():
    filtros = {
        "email": request.args.get('email'),
        "nombre": request.args.get('nombre'),
        "telefono_pais": request.args.get('telefono_pais'),
        "telefono_numero_local": request.args.get('telefono_numero_local'),
        "rol": request.args.get('rol')
    }

    try:
        usuarios_filtrados = filtrar_usuarios_service(filtros)
        return jsonify(usuarios_filtrados), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
@usuarios_bp.route('/usuario/<int:id_usuario>', methods=['DELETE'])
def eliminar_usuario(id_usuario):
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    db.session.delete(usuario)
    db.session.commit()

    return jsonify({'mensaje': f'Usuario {usuario.nombre} eliminado correctamente'}), 200


#endpoint para obtener los datos de un usuario por el uid (usando en la interface de configuraciones de perfil)
@usuarios_bp.route('/api/userconfig', methods=['GET'])
def user_config():
    auth_header = request.headers.get('Authorization', '')

    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token no proporcionado o malformado'}), 401

    id_token = auth_header.split('Bearer ')[1]

    try:
        # Validar token y extraer uid
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token.get('uid')

        if not uid:
            return jsonify({'error': 'Token inválido, sin uid'}), 401

        # Buscar usuario por uid
        usuario = obtener_usuario_por_uid(uid)
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Devolver datos completos del usuario
        return jsonify(usuario), 200

    except Exception as e:
        return jsonify({'error': 'Token inválido o expirado', 'detalle': str(e)}), 401