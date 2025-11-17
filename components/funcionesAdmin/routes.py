#endpoints que solo necesitara el adminitrador
# components/funcionesAdmin/routes.py
from flask import Blueprint, request, jsonify
from core.models import db, Usuario
from components.funcionesAdmin.services import actualizar_datos_usuario
from firebase_admin import auth


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


@admin_bp.route('/admin/usuarios/<int:id_usuario>/suspender', methods=['PATCH'])
def suspender_usuario(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)
    try:
        auth.update_user(usuario.firebase_uid, disabled=True)
        usuario.estado = "suspendido"
        db.session.commit()
        return jsonify({
            "mensaje": f"Usuario {usuario.nombre} suspendido correctamente",
            "usuario": {"id": usuario.id, "estado": usuario.estado}
        }), 200
    except Exception as error:
        return jsonify({"error": f"No se pudo suspender al usuario: {str(error)}"}), 500


@admin_bp.route('/admin/usuarios/<int:id_usuario>/activar', methods=['PATCH'])
def activar_usuario(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)
    try:
        auth.update_user(usuario.firebase_uid, disabled=False)
        usuario.estado = "activo"
        db.session.commit()
        return jsonify({
            "mensaje": f"Usuario {usuario.nombre} activado correctamente",
            "usuario": {"id": usuario.id, "estado": usuario.estado}
        }), 200
    except Exception as error:
        return jsonify({"error": f"No se pudo activar al usuario: {str(error)}"}), 500