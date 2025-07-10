from flask import Blueprint, request, jsonify
from notificaciones.services import (
    crear_notificacion,
    obtener_notificaciones_por_usuario,
    obtener_todas,
    marcar_notificacion_como_leida,
    eliminar_notificacion
)

notificaciones_bp = Blueprint("notificaciones", __name__)

@notificaciones_bp.route("/notificaciones", methods=["POST"])
def crear():
    data = request.get_json()
    return crear_notificacion(data)


@notificaciones_bp.route("/notificaciones/<int:id_usuario>", methods=["GET"])
def get_por_usuario(id_usuario):
    solo_no_leidas = request.args.get("solo_no_leidas", "false").lower() == "true"
    notis = obtener_notificaciones_por_usuario(id_usuario, solo_no_leidas)
    return jsonify(notis), 200

@notificaciones_bp.route("/notificaciones", methods=["GET"])
def get_todo():
    notis = obtener_todas()
    return jsonify(notis), 200


@notificaciones_bp.route("/notificaciones/leida/<int:id_noti>", methods=["PATCH"])
def marcar_leida(id_noti):
    return jsonify(marcar_notificacion_como_leida(id_noti)), 200


@notificaciones_bp.route("/notificaciones/<int:id_noti>", methods=["DELETE"])
def eliminar(id_noti):
    return jsonify(eliminar_notificacion(id_noti)), 200
