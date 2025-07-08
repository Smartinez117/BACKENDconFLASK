from flask import Blueprint, request, jsonify
from publicaciones.services import crear_publicacion, obtener_publicaciones

publicaciones_bp = Blueprint("publicaciones", __name__)

@publicaciones_bp.route("/publicaciones", methods=["POST"])
def crear():
    data = request.get_json()
    return crear_publicacion(data)

@publicaciones_bp.route("/publicaciones", methods=["GET"])
def obtener():
    categoria = request.args.get("categoria")
    return obtener_publicaciones(categoria)
