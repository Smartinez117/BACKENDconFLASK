from flask import Blueprint, request, jsonify
from core.models import db, Usuario
from usuarios.services import actualizar_datos_usuario , get_usuario

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/usuario/<int:id_usuario>', methods=['PATCH'])
def actualizar_usuario(id_usuario):
    data = request.get_json()
    try:
     actualizar_datos_usuario(id_usuario,data)
     return jsonify({'mensaje': 'Usuario actualizado con éxito'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@usuarios_bp.route('/usuario/<int:id_usuario>', methods = ['GET'])
def obtener_usuario_por_id(id_usuario):
   usuario = get_usuario(id_usuario) 
   return jsonify(usuario), 200

@usuarios_bp.route('/api/usuarios/ban', methods=['PATCH'])
def banear_usuario():
   data = request.get_json()
   
   usuario_baneado = get_usuario(id_ban)
   
   if usuario_baneado.rol == "admin":
        return jsonify({"error": "No se puede banear a otro administrador"}), 403

   usuario_baneado.rol = "baneado"
   db.session.commit()

   return jsonify({"mensaje": f"Usuario {usuario_baneado.nombre} baneado correctamente"}), 200