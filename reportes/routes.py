from flask import Blueprint, request, jsonify
from reportes.services import (
    crear_reporte,
    obtener_reportes_por_publicacion,
    obtener_reportes_por_usuario,
    obtener_todos_los_reportes,
    obtener_usuarios_con_posts_reportados,
    eliminar_reporte
)

reportes_bp = Blueprint("reportes", __name__)

# Crear reporte
@reportes_bp.route("/reportes", methods=["POST"])
def crear():
    data = request.get_json()
    return crear_reporte(data)



# Obtener todos los reportes
@reportes_bp.route("/reportes", methods=["GET"])
def get_todos():
    return jsonify(obtener_todos_los_reportes()), 200

# Obtener reportes por publicación
@reportes_bp.route("/reportes/publicacion/<int:id_publicacion>", methods=["GET"])
def get_por_publicacion(id_publicacion):
    return jsonify(obtener_reportes_por_publicacion(id_publicacion)), 200

# Obtener reportes hechos por un usuario
@reportes_bp.route("/reportes/usuario/<int:id_usuario>", methods=["GET"])
def get_por_usuario(id_usuario):
    return jsonify(obtener_reportes_por_usuario(id_usuario)), 200

# Obtener usuarios con publicaciones reportadas
@reportes_bp.route("/reportes/usuarios-reportados", methods=["GET"])
def get_usuarios_con_posts_reportados():
    return jsonify(obtener_usuarios_con_posts_reportados()), 200



# Eliminar reporte
@reportes_bp.route("/reportes/<int:id_reporte>", methods=["DELETE"])
def eliminar(id_reporte):
    return jsonify(eliminar_reporte(id_reporte)), 200
