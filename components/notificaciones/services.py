from core.models import db, Notificacion,Publicacion
from datetime import datetime,timezone
#from routes import userconnected
from ..usuarios.routes import userconnected  #importamos la libreria de usuarios conectados
from util import socketio
from ..usuarios.services import get_usuario
import pytz
zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")

def crear_notificacion(data):#suponog que aca habria que agregar lo del id de la publicacion
    """Crea una nueva notificación en la base de datos."""
    try:
        nueva = Notificacion(
            id_usuario=data['id_usuario'],
            titulo=data.get('titulo'),
            descripcion=data.get('descripcion'),
            tipo=data.get('tipo'),
            fecha_creacion=datetime.now(timezone.utc),
            leido=False
        )
        db.session.add(nueva)
        db.session.commit()
        return {"mensaje": "Notificación creada", "id": nueva.id}, 201
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


def obtener_notificaciones_por_usuario(id_usuario, solo_no_leidas=False):
    """Obtiene todas las notificaciones de un usuario, opcionalmente solo las no leídas."""
    query = Notificacion.query.filter_by(id_usuario=id_usuario)
    if solo_no_leidas:
        query = query.filter_by(leido=False)
    return [noti_to_dict(n) for n in query.order_by(Notificacion.fecha_creacion.desc()).all()]


def obtener_todas():
    """Obtiene todas las notificaciones de la base de datos."""
    query = Notificacion.query.order_by(Notificacion.fecha_creacion.desc()).all()
    return [noti_to_dict(n) for n in query]


def marcar_notificacion_como_leida(id_noti):
    """Marca una notificación como leída por su ID."""
    noti = Notificacion.query.get(id_noti)
    if not noti:
        return {"error": "No encontrada"}, 404
    noti.leido = True
    db.session.commit()
    return {"mensaje": "Notificación marcada como leída"}



def eliminar_notificacion(id_noti):
    """Elimina una notificación de la base de datos por su ID."""
    noti = Notificacion.query.get(id_noti)
    if not noti:
        return {"error": "No encontrada"}, 404
    db.session.delete(noti)
    db.session.commit()
    return {"mensaje": "Notificación eliminada"}


def noti_to_dict(n):
    """Convierte una notificación a un diccionario serializable."""
    ahora = datetime.now(timezone.utc)
    delta = ahora - n.fecha_creacion

    if delta.days > 0:
        tiempo_pasado = f"hace {delta.days} día(s)"
    elif delta.seconds >= 3600:
        tiempo_pasado = f"hace {delta.seconds // 3600} hora(s)"
    elif delta.seconds >= 60:
        tiempo_pasado = f"hace {delta.seconds // 60} minuto(s)"
    else:
        tiempo_pasado = "hace unos segundos"

    return {
        "id": n.id,
        "id_usuario": n.id_usuario,
        "titulo": n.titulo,
        "descripcion": n.descripcion,
        "tipo": n.tipo,
        "fecha_creacion": n.fecha_creacion.isoformat(),
        "tiempo_pasado": tiempo_pasado,
        "leido": n.leido
    }

#funciones para las notficaiones de los sockets
#aqui voy a definir dos eventos que creo que son los unicos asique vamos a verlos despues

#en caso de que ocurra el evento de que alguien comenta tu publicacion entonces notificas de inmediato
#iria de la mano con la funcion de crear notificacion asique la dejare aqui notado 
def notificar(newnotificacion):
    """Envía una notificación en tiempo real al usuario correspondiente usando sockets."""
    id_owner = obtener_user_por_idpublicacion(newnotificacion.id_publicacion)
    user = get_usuario(id_owner)
    uid_user= user.firebase_uid
    if  uid_user in userconnected:     
        notification = {
            "titulo": newnotificacion.titulo,
            "descripcion": newnotificacion.descripcion,
            "id_publicacion" :newnotificacion.id_publicacion, # para redirigir al user a la publicacion si quiere ver quien corno comento algo 
            "id_notificacion": newnotificacion.id  #para marcarla como leida
        }
        socketio.emit('notificacion',notification,namespace='/notificacion/'+uid_user) 

#en caso de que te conectes entonces le pides al back todas tus notificaciones:
#esta la tendria que importar en la parte que cree para registrar a los user en la carpeta de users
#voy a reutilizar las funciones que ya estand definidas
def notificarconectado(iduser,uid_user):
    """Envía todas las notificaciones pendientes a un usuario conectado."""
    notificaciones_pendientes = obtener_notificaciones_por_usuario(iduser)
    if notificaciones_pendientes and uid_user in userconnected:
        for notification in notificaciones_pendientes:
            socketio.emit('notificacion',notification,namespace='/notificacion/'+uid_user) 
#esta va a enviar todas las notificaciones pendientes que tiene la cosa incluso podemos enviarlas en orden soo modificando el query

def obtener_user_por_idpublicacion(publicacionID):
    """Obtiene el ID de usuario dueño de una publicación dado el ID de la publicación."""
    publicacion = Publicacion.query(publicacionID)
    if publicacion:
        return publicacion.id_usuario
