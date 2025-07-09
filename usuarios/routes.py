from flask import Blueprint, request, jsonify
from core.models import db, Usuario
from usuarios.services import actualizar_datos_usuario

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/usuario/<int:id_usuario>', methods=['PATCH'])
def actualizar_usuario(id_usuario):
    data = request.get_json()
    try:
     actualizar_datos_usuario(id_usuario,data)
     return jsonify({'mensaje': 'Usuario actualizado con éxito'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
