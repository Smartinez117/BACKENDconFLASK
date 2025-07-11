from flask import Blueprint, jsonify, request
from imagenes.services import obtener_todas_las_imagenes, obtener_imagenes_por_publicacion,crear_imagen,eliminar_imagen

imagenes_bp = Blueprint("imagenes", __name__)

# GET /imagenes
@imagenes_bp.route("/imagenes", methods=["GET"])
def get_todas_las_imagenes():
    return jsonify(obtener_todas_las_imagenes()), 200

# GET /imagenes/publicacion/<int:id_publicacion>
@imagenes_bp.route("/imagenes/publicacion/<int:id_publicacion>", methods=["GET"])
def get_imagenes_de_publicacion(id_publicacion):
    return jsonify(obtener_imagenes_por_publicacion(id_publicacion)), 200


# POST /imagenes
@imagenes_bp.route("/imagenes", methods=["POST"])
def crear_imagen():
    data = request.get_json()
    return crear_imagen(data)

# DELETE /imagenes/<int:id_imagen>
@imagenes_bp.route("/imagenes/<int:id_imagen>", methods=["DELETE"])
def eliminar_imagen(id_imagen):
    return eliminar_imagen(id_imagen)