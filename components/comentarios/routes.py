from flask import Blueprint, request, jsonify, g
from components.comentarios.services import (
    crear_comentario,
    obtener_comentarios_por_publicacion,
    obtener_comentario_por_su_id,
    obtener_todos,
    actualizar_comentario,
    eliminar_comentario
)
from auth.services import require_auth

comentarios_bp = Blueprint("comentarios", __name__)

@comentarios_bp.route("/comentarios", methods=["POST"])
@require_auth
def crear():
    """Crea un nuevo comentario."""
    data = request.get_json()
    data["id_usuario"] = g.usuario_actual.id
    return crear_comentario(data)


@comentarios_bp.route("/comentarios/publicacion/<int:id_publicacion>", methods=["GET"])
def get_comentario_por_id_publicacion(id_publicacion):
    """Obtiene comentarios por ID de publicación."""
    return jsonify(obtener_comentarios_por_publicacion(id_publicacion)), 200


@comentarios_bp.route("/comentarios/<int:id_comentario>", methods=["GET"])
def get_comentario_por_su_id(id_comentario):
    """Obtiene un comentario por su ID."""
    comentario = obtener_comentario_por_su_id(id_comentario)
    if comentario:
        return jsonify(comentario), 200
    else:
        return jsonify({'error': 'Comentario no encontrado'}), 404


@comentarios_bp.route("/comentarios", methods=["GET"])
def get_comentarios():
    """Obtiene todos los comentarios."""
    return jsonify(obtener_todos()), 200



@comentarios_bp.route("/comentarios/<int:id_comentario>", methods=["PATCH"])
def actualizar(id_comentario):
    """Actualiza un comentario existente."""
    try:
        data = request.get_json()
        actualizar_comentario(id_comentario, data)
        return jsonify({"mensaje": "Comentario actualizado"}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@comentarios_bp.route("/comentarios/<int:id_comentario>", methods=["DELETE"])
def eliminar(id_comentario):
    """Elimina un comentario por su ID."""
    try:
        eliminar_comentario(id_comentario)
        return jsonify({"mensaje": "Comentario eliminado"}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 400
