from flask import Blueprint, request, jsonify, g
from components.notificaciones.services import (
    crear_notificacion,
    obtener_notificaciones_por_usuario,
    obtener_todas,
    marcar_notificacion_como_leida,
    eliminar_notificacion
)
from auth.services import require_auth

notificaciones_bp = Blueprint("notificaciones", __name__)

@notificaciones_bp.route("/notificaciones", methods=["POST"])
# @require_auth  <-- Opcional: Descomentar si solo usuarios logueados pueden crear notificaciones
def crear():
    """Crea una nueva notificación (ej: cuando alguien comenta)."""
    data = request.get_json()
    # Aquí podrías validar que data tenga 'id_usuario' (el receptor)
    return crear_notificacion(data)


@notificaciones_bp.route("/notificaciones/usuario", methods=["GET"])
@require_auth
def get_por_usuario():
    """
    El frontend llamará a esto periódicamente (Polling).
    """
    usuario_id = g.usuario_actual.id
    solo_no_leidas = request.args.get("solo_no_leidas", "false").lower() == "true"
    
    notis = obtener_notificaciones_por_usuario(usuario_id, solo_no_leidas)
    return jsonify(notis), 200


@notificaciones_bp.route("/notificaciones", methods=["GET"])
def get_todo():
    """Admin: Obtiene todas."""
    notis = obtener_todas()
    return jsonify(notis), 200


@notificaciones_bp.route("/notificaciones/leida/<int:id_noti>", methods=["PATCH"])
@require_auth
def marcar_leida(id_noti):
    """Marca una notificación como leída."""
    return jsonify(marcar_notificacion_como_leida(id_noti))


@notificaciones_bp.route("/notificaciones/<int:id_noti>", methods=["DELETE"])
@require_auth
def eliminar(id_noti):
    """Elimina una notificación."""
    return jsonify(eliminar_notificacion(id_noti))