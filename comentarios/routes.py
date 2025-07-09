from flask import Blueprint, request, jsonify
from comentarios.services import (
    crear_comentario,
    obtener_comentarios_por_publicacion,
    obtener_comentario_por_su_id,
    obtener_todos,
    actualizar_comentario,
    eliminar_comentario
)

comentarios_bp = Blueprint("comentarios", __name__)

@comentarios_bp.route("/comentarios", methods=["POST"])
def crear():
    data = request.get_json()
    return crear_comentario(data)


@comentarios_bp.route("/comentarios/publicacion/<int:id_publicacion>", methods=["GET"])
def get_comentario_por_id_publicacion(id_publicacion):
    return jsonify(obtener_comentarios_por_publicacion(id_publicacion)), 200


@comentarios_bp.route("/comentarios/<int:id_comentario>", methods=["GET"])
def get_comentario_por_su_id(id_comentario):
    comentario = obtener_comentario_por_su_id(id_comentario)
    if comentario:
        return jsonify(comentario), 200
    else:
        return jsonify({'error': 'Comentario no encontrado'}), 404


@comentarios_bp.route("/comentarios", methods=["GET"])
def get_comentarios():
    return jsonify(obtener_todos()), 200



@comentarios_bp.route("/comentarios/<int:id_comentario>", methods=["PATCH"])
def actualizar(id_comentario):
    try:
        data = request.get_json()
        actualizar_comentario(id_comentario, data)
        return jsonify({"mensaje": "Comentario actualizado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@comentarios_bp.route("/comentarios/<int:id_comentario>", methods=["DELETE"])
def eliminar(id_comentario):
    try:
        eliminar_comentario(id_comentario)
        return jsonify({"mensaje": "Comentario eliminado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
