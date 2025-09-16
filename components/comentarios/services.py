from datetime import datetime, timezone
from core.models import db, Comentario, Publicacion, Notificacion,Usuario
from components.notificaciones.services import crear_notificacion
import pytz

zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")


def crear_comentario(data):
    """Crea un nuevo comentario y, si corresponde, una notificación al autor de la publicación."""
    try:
        nuevo = Comentario(
            id_publicacion=data['id_publicacion'],
            id_usuario=data['id_usuario'],
            id_anterior=data.get('id_anterior'),
            descripcion=data['descripcion'],
            fecha_creacion=datetime.now(timezone.utc),
            fecha_modificacion=datetime.now(timezone.utc)
        )
        db.session.add(nuevo)

        # Obtener datos necesarios
        publicacion = Publicacion.query.get(data['id_publicacion'])
        usuario_comentador = Usuario.query.get(data['id_usuario'])

        if publicacion and usuario_comentador and int(publicacion.id_usuario) != int(usuario_comentador.id):
            # Usar la función reutilizable para crear la notificación
            crear_notificacion({
                "id_usuario": publicacion.id_usuario,
                "titulo": f"{usuario_comentador.nombre} comentó tu publicación",
                "descripcion": f"Comentó en: '{publicacion.titulo}'",
                "tipo": "comentario"
            })

        db.session.commit()
        return {"mensaje": "Comentario creado", "id": nuevo.id}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400



def obtener_comentarios_por_publicacion(id):
    """Obtiene todos los comentarios asociados a una publicación por su ID."""
    comentarios = Comentario.query.filter_by(id_publicacion=id).all()
    resultado = []
    for c in comentarios:
        resultado.append({
            "id": c.id,
            "id_usuario": c.id_usuario,
            "descripcion": c.descripcion,
            "fecha_creacion": (
                c.fecha_creacion.astimezone(zona_arg).isoformat()
                if c.fecha_creacion else None
            ),
            "fecha_modificacion": (
                c.fecha_modificacion.astimezone(zona_arg).isoformat()
                if c.fecha_modificacion else None
            ),
            "id_anterior": c.id_anterior
        })
    return resultado


def obtener_comentario_por_su_id(id_comentario):
    """Obtiene un comentario específico por su ID."""
    comentario = Comentario.query.get(id_comentario)

    if not comentario:
        return None

    return {
        'id': comentario.id,
        'id_publicacion': comentario.id_publicacion,
        'id_usuario': comentario.id_usuario,
        'id_anterior': comentario.id_anterior,
        'descripcion': comentario.descripcion,
        'fecha_creacion': (
            comentario.fecha_creacion.astimezone(zona_arg).isoformat()
            if comentario.fecha_creacion else None
        ),
        'fecha_modificacion': (
            comentario.fecha_modificacion.astimezone(zona_arg).isoformat()
            if comentario.fecha_modificacion else None
        )
    }
    
def obtener_todos():
    """Obtiene todos los comentarios de la base de datos."""
    comentarios = Comentario.query.all()
    resultado = []
    if not comentarios:
        return None

    for comentario in comentarios:
        resultado.append({
            'id': comentario.id,
            'id_publicacion': comentario.id_publicacion,
            'id_usuario': comentario.id_usuario,
            'id_anterior': comentario.id_anterior,
            'descripcion': comentario.descripcion,
            'fecha_creacion': (
                comentario.fecha_creacion.astimezone(zona_arg).isoformat()
                if comentario.fecha_creacion else None
            ),
            'fecha_modificacion': (
                comentario.fecha_modificacion.astimezone(zona_arg).isoformat()
                if comentario.fecha_modificacion else None
            )
        })
    return resultado


def actualizar_comentario(id_comentario, data):
    """Actualiza la descripción y la fecha de modificación de un comentario."""
    comentario = Comentario.query.get(id_comentario)
    if not comentario:
        raise Exception("Comentario no encontrado")

    comentario.descripcion = data.get("descripcion", comentario.descripcion)
    comentario.fecha_modificacion = datetime.now(timezone.utc)

    db.session.commit()


def eliminar_comentario(id_comentario):
    """Elimina un comentario de la base de datos por su ID."""
    comentario = Comentario.query.get(id_comentario)
    if not comentario:
        raise Exception("Comentario no encontrado")

    db.session.delete(comentario)
    db.session.commit()
