from flask import Blueprint, request, jsonify
from core.models import db, Usuario
from usuarios.services import actualizar_datos_usuario , get_usuario,filtrar_usuarios_service

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
def banear_usuario(id_usuario):

    usuario = Usuario.query.get_or_404(id_usuario)

    if usuario.rol == "admin":
        return jsonify({"error": "No se puede banear a otro administrador"}), 403

    usuario.rol = "baneado"
    db.session.commit()

    return jsonify({"mensaje": f"Usuario {usuario.nombre} baneado correctamente"}), 200



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