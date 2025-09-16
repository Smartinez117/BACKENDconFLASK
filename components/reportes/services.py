from datetime import datetime,timezone
from core.models import db, Reporte, Publicacion, Usuario
import pytz
zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")

def crear_reporte(data):
    '''Crea un nuevo reporte en la base de datos.'''
    try:
        nuevo = Reporte(
            id_publicacion=data['id_publicacion'],
            id_usuario=data['id_usuario'],
            descripcion=data.get('descripcion'),
            tipo=data.get('tipo'),
            fecha_creacion=datetime.now(timezone.utc)
        )
        db.session.add(nuevo)
        db.session.commit()
        return {"mensaje": "Reporte creado", "id": nuevo.id}, 201
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400



def obtener_todos_los_reportes():
    '''Obtiene todos los reportes de la base de datos.'''
    reportes = (
        Reporte.query.order_by(Reporte.fecha_creacion.desc()).all()
    )
    return [reporte_to_dict(r) for r in reportes]

def obtener_reportes_por_publicacion(id_publicacion):
    '''Obtiene reportes asociados a una publicación específica.'''
    reportes = (
        Reporte.query.filter_by(id_publicacion=id_publicacion)
        .order_by(Reporte.fecha_creacion.desc()).all()
    )
    return [reporte_to_dict(r) for r in reportes]

def obtener_reportes_por_usuario(id_usuario):
    '''Obtiene reportes hechos por un usuario específico.'''
    reportes = (
        Reporte.query.filter_by(id_usuario=id_usuario)
        .order_by(Reporte.fecha_creacion.desc()).all()
    )
    return [reporte_to_dict(r) for r in reportes]

def obtener_usuarios_con_posts_reportados():
    '''Obtiene usuarios que tienen publicaciones reportadas.'''
    # Buscar publicaciones que tienen al menos un reporte
    publicaciones_reportadas = (
        db.session.query(Publicacion.id, Publicacion.id_usuario)
        .join(Reporte, Reporte.id_publicacion == Publicacion.id)
        .all()
    )

    # Agrupar por usuario
    usuarios_reportados = {}
    for pub_id, user_id in publicaciones_reportadas:
        if user_id not in usuarios_reportados:
            usuarios_reportados[user_id] = []
        usuarios_reportados[user_id].append(pub_id)

    # Transformar a lista de diccionarios
    resultado = [
        {"id_usuario": user_id, "publicaciones_reportadas": pubs}
        for user_id, pubs in usuarios_reportados.items()
    ]

    return resultado


def eliminar_reporte(id_reporte):
    '''Elimina un reporte por su ID.'''
    reporte = Reporte.query.get(id_reporte)
    if not reporte:
        return {"error": "Reporte no encontrado"}, 404
    db.session.delete(reporte)
    db.session.commit()
    return {"mensaje": "Reporte eliminado"}



def reporte_to_dict(r):
    '''Convierte un objeto Reporte a un diccionario.'''
    return {
        "id": r.id,
        "id_publicacion": r.id_publicacion,
        "id_usuario": r.id_usuario,
        "descripcion": r.descripcion,
        "tipo": r.tipo,
        "fecha_creacion": (
            r.fecha_creacion.astimezone(zona_arg).isoformat()
            if r.fecha_creacion else None
        )
    }
