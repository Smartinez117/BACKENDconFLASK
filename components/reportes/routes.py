from flask import Blueprint, request, jsonify,g
from components.reportes.services import (
    crear_reporte,
    obtener_reportes_por_publicacion,
    obtener_reportes_por_usuario,
    obtener_todos_los_reportes,
    obtener_usuarios_con_posts_reportados,
    eliminar_reporte
)
from auth.services import require_auth

reportes_bp = Blueprint("reportes", __name__)

# Crear reporte
@reportes_bp.route("/reportes", methods=["POST"])
@require_auth
def crear():
    '''Crea un nuevo reporte.'''
    data = request.get_json()
    data['id_usuario'] = g.usuario_actual.id
    return crear_reporte(data)



# Obtener todos los reportes
@reportes_bp.route("/reportes", methods=["GET"])
def get_todos():
    '''Obtiene todos los reportes.'''
    return jsonify(obtener_todos_los_reportes()), 200

# Obtener reportes por publicación
@reportes_bp.route("/reportes/publicacion/<int:id_publicacion>", methods=["GET"])
def get_por_publicacion(id_publicacion):
    '''Obtiene reportes asociados a una publicación específica.'''
    return jsonify(obtener_reportes_por_publicacion(id_publicacion)), 200

# Obtener reportes hechos por un usuario
@reportes_bp.route("/reportes/usuario/<int:id_usuario>", methods=["GET"])
def get_por_usuario(id_usuario):
    '''Obtiene reportes hechos por un usuario específico.'''
    return jsonify(obtener_reportes_por_usuario(id_usuario)), 200

# Obtener usuarios con publicaciones reportadas
@reportes_bp.route("/reportes/usuarios-reportados", methods=["GET"])
def get_usuarios_con_posts_reportados():
    '''Obtiene usuarios que tienen publicaciones reportadas.'''
    return jsonify(obtener_usuarios_con_posts_reportados()), 200

# Eliminar reporte
@reportes_bp.route("/reportes/<int:id_reporte>", methods=["DELETE"])
def eliminar(id_reporte):
    '''Elimina un reporte por su ID.'''
    return jsonify(eliminar_reporte(id_reporte)), 200
