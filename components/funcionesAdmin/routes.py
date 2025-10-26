#endpoints que solo necesitara el adminitrador
# components/funcionesAdmin/routes.py
from flask import Blueprint, request, jsonify
from core.models import db, Usuario
from components.funcionesAdmin.services import actualizar_datos_usuario

# Blueprint exclusivo para funciones de admin
admin_bp = Blueprint('admin', __name__)

# Endpoint para que el admin actualice nombre y rol de un usuario
@admin_bp.route('/admin/usuario/<int:id_usuario>', methods=['PATCH'])
def admin_actualizar_usuario(id_usuario):
    """
    Permite al administrador actualizar únicamente el nombre y rol de un usuario.
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se enviaron datos'}), 400

    try:
        usuario_actualizado = actualizar_datos_usuario(id_usuario, data)
        if not usuario_actualizado:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        return jsonify(usuario_actualizado), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

