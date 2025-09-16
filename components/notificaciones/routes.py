from flask import Blueprint, request, jsonify , g
from components.notificaciones.services import (
    crear_notificacion,
    obtener_notificaciones_por_usuario,
    obtener_todas,
    marcar_notificacion_como_leida,
    eliminar_notificacion
)
from auth.services import require_auth
#
from util import socketio
from ..usuarios.routes import userconnected  #importamos la libreria de usuarios conectados
#importaciones para las pruebas
#importaciones para las pruebas

notificaciones_bp = Blueprint("notificaciones", __name__)

@notificaciones_bp.route("/notificaciones", methods=["POST"])
def crear():
    """Crea una nueva notificación."""
    data = request.get_json()
    return crear_notificacion(data)


@notificaciones_bp.route("/notificaciones/usuario", methods=["GET"])
@require_auth
def get_por_usuario():
    """Obtiene las notificaciones de un usuario autenticado."""
    usuario = g.usuario_actual.id
    solo_no_leidas = request.args.get("solo_no_leidas", "false").lower() == "true"
    notis = obtener_notificaciones_por_usuario(usuario, solo_no_leidas)
    return jsonify(notis), 200

@notificaciones_bp.route("/notificaciones", methods=["GET"])
def get_todo():
    """Obtiene todas las notificaciones."""
    notis = obtener_todas()
    notis = obtener_todas()
    return jsonify(notis), 200


@notificaciones_bp.route("/notificaciones/leida/<int:id_noti>", methods=["PATCH"])
def marcar_leida(id_noti):
    """Marca una notificación como leída por su ID."""
    return jsonify(marcar_notificacion_como_leida(id_noti)), 200


@notificaciones_bp.route("/notificaciones/<int:id_noti>", methods=["DELETE"])
def eliminar(id_noti):
    """Elimina una notificación por su ID."""
    return jsonify(eliminar_notificacion(id_noti)), 200

#notificaciones en tiempo real
@notificaciones_bp.route("/notificacion", methods=["POST"])
def crear_con_socket():
    """Crea una notificación y la envía en tiempo real por socket."""
    data = request.get_json()
    # lógica para crear notificación -->
    socketio.emit("nueva_notificacion", {"mensaje": "Nueva notificación"})
    return jsonify({"status": "ok"}), 200

#datos de prueba para la part de notificaicones---------------------------------------------
notification = {
            "titulo": "lautaro stuve comento tu publicacion",
            "descripcion": "comento en 'perro marron perdido",
            "id_publicacion" : "76", # para redirigir al user a la publicacion 
            "id_notificacion": "12"  #para marcarla como leida aunque en esta prueba, todavia no definida en front
        }
mensaje = {
  "titulo": "lautaro stuve comento tu publicacion",
  "descripcion": "comento en 'perro marron perdido'"
}
uid= 'abve72UPGJZWfSfvx3KGBqd0UGf1'


@socketio.on('connect', namespace='/notificacion/'+uid)
def on_connect():
    """Maneja la conexión de un cliente al namespace de notificaciones."""
    print('Cliente conectado al namespace')

@notificaciones_bp.route("/pruebanot", methods=["POST"])
def crear_con_socket1():
    """Crea una notificación de prueba y la envía por socket."""
    data = request.get_json()
    # lógica para crear notificación -->
    #notificar(notification)
    socketio.emit('notificacion',notification,namespace='/notificacion/'+uid) #una vez
    return jsonify({"status": "ok"}), 200

#datos de prueba para la part de notificaciones---------------------------------
