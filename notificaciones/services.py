from core.models import db, Notificacion
from datetime import datetime

def crear_notificacion(data):
    try:
        nueva = Notificacion(
            id_usuario=data['id_usuario'],
            titulo=data.get('titulo'),
            descripcion=data.get('descripcion'),
            tipo=data.get('tipo'),
            fecha_creacion=datetime.utcnow(),
            leido=False
        )
        db.session.add(nueva)
        db.session.commit()
        return {"mensaje": "Notificación creada", "id": nueva.id}, 201
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


def obtener_notificaciones_por_usuario(id_usuario, solo_no_leidas=False):
    query = Notificacion.query.filter_by(id_usuario=id_usuario)
    if solo_no_leidas:
        query = query.filter_by(leido=False)
    return [noti_to_dict(n) for n in query.order_by(Notificacion.fecha_creacion.desc()).all()]


def obtener_todas():
    query = Notificacion.query.order_by(Notificacion.fecha_creacion.desc()).all()
    return [noti_to_dict(n) for n in query]


def marcar_notificacion_como_leida(id_noti):
    noti = Notificacion.query.get(id_noti)
    if not noti:
        return {"error": "No encontrada"}, 404
    noti.leido = True
    db.session.commit()
    return {"mensaje": "Notificación marcada como leída"}



def eliminar_notificacion(id_noti):
    noti = Notificacion.query.get(id_noti)
    if not noti:
        return {"error": "No encontrada"}, 404
    db.session.delete(noti)
    db.session.commit()
    return {"mensaje": "Notificación eliminada"}


def noti_to_dict(n):
    ahora = datetime.utcnow()
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