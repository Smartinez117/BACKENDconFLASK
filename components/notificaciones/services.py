from core.models import db, Notificacion, Publicacion
from datetime import datetime, timezone
from ..usuarios.services import get_usuario
import pytz

zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")

def crear_notificacion(data):
    """
    Crea una nueva notificación en la base de datos.
    Ya no emite sockets, solo guarda la info para que el usuario la consulte.
    """
    try:
        nueva = Notificacion(
            id_usuario=data['id_usuario'],
            titulo=data.get('titulo'),
            descripcion=data.get('descripcion'),
            tipo=data.get('tipo'), # Ej: 'comentario', 'solicitud', 'sistema'
            fecha_creacion=datetime.now(timezone.utc),
            leido=False,
            id_publicacion=data.get('id_publicacion'),
            id_referencia=data.get('id_referencia') # Importante para solicitudes
        )
        db.session.add(nueva)
        db.session.commit()
    
        return {"mensaje": "Notificación creada", "id": nueva.id}, 201
        
    except Exception as error:
        db.session.rollback()
        print(f"Error al crear notificación: {error}")
        return {"error": str(error)}, 400


def obtener_notificaciones_por_usuario(id_usuario, solo_no_leidas=False):
    """
    Esta es la función que llamará el Frontend cada X segundos.
    """
    query = Notificacion.query.filter_by(id_usuario=id_usuario)
    
    if solo_no_leidas:
        query = query.filter_by(leido=False)
        
    # Ordenamos por las más recientes primero
    notificaciones = query.order_by(Notificacion.fecha_creacion.desc()).limit(50).all()
    
    return [n.to_dict() for n in notificaciones]


def obtener_todas():
    query = Notificacion.query.order_by(Notificacion.fecha_creacion.desc()).all()
    # Reutilizamos el to_dict del modelo para ser consistentes
    return [n.to_dict() for n in query]


def marcar_notificacion_como_leida(id_noti):
    noti = Notificacion.query.get(id_noti)
    if not noti:
        return {"error": "No encontrada"}, 404
    
    noti.leido = True
    db.session.commit()
    return {"mensaje": "Notificación marcada como leída", "id": id_noti}


def eliminar_notificacion(id_noti):
    noti = Notificacion.query.get(id_noti)
    if not noti:
        return {"error": "No encontrada"}, 404
    
    db.session.delete(noti)
    db.session.commit()
    return {"mensaje": "Notificación eliminada"}

# --- UTILIDADES ---

def obtener_user_por_idpublicacion(publicacion_id):
    publicacion = Publicacion.query.get(publicacion_id)
    if publicacion:
        return publicacion.id_usuario
    return None