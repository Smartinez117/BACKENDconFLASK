from datetime import datetime, timezone
from core.models import db, Reporte, Publicacion, Usuario
import pytz

zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")

# --- TU FUNCIÓN CREAR (YA ESTABA BIEN) ---
def crear_reporte(data):
    try:
        id_pub = data.get('id_publicacion')
        id_com = data.get('id_comentario')
        id_usu_rep = data.get('id_usuario_reportado')

        if not any([id_pub, id_com, id_usu_rep]):
            return {"error": "Debe especificar qué está reportando"}, 400

        nuevo_reporte = Reporte(
            id_usuario=data['id_usuario'],
            id_publicacion=id_pub,
            id_comentario=id_com,
            id_usuario_reportado=id_usu_rep,
            descripcion=data.get('descripcion'),
            tipo=data.get('tipo'),
            fecha_creacion=datetime.now(timezone.utc)
        )

        db.session.add(nuevo_reporte)
        db.session.commit()

        return {"mensaje": "Reporte creado con éxito", "id": nuevo_reporte.id}, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500

# --- TU FUNCIÓN OBTENER TODOS (YA ESTABA BIEN) ---
def obtener_todos_los_reportes():
    reportes = Reporte.query.order_by(Reporte.fecha_creacion.desc()).all()
    return [reporte_to_dict(r) for r in reportes]

# --- CORRECCIÓN: FUNCIÓN UNIFICADA DE SERIALIZACIÓN ---
def reporte_to_dict(r):
    '''Convierte un objeto Reporte a un diccionario completo.'''
    
    # Determinar tipo de objetivo
    objetivo_tipo = "Desconocido"
    objetivo_id = None
    objetivo_slug = None
    
    
    if r.id_comentario:
        objetivo_tipo = "Comentario"
        objetivo_id = r.id_comentario
        objetivo_slug = r.id_publicacion
    elif r.id_publicacion:
        objetivo_tipo = "Publicación"
        objetivo_id = r.id_publicacion
    elif r.id_usuario_reportado:
        objetivo_tipo = "Usuario"
        objetivo_id = r.id_usuario_reportado
        if r.denunciado: 
            objetivo_slug = r.denunciado.slug
        else:
            # Fallback por si el usuario fue borrado pero el reporte quedó
            objetivo_slug = r.id_usuario_reportado

    return {
        "id": r.id,
        "id_usuario_denunciante": r.id_usuario,
        "descripcion": r.descripcion,
        "tipo_reporte": r.tipo,
        "fecha_creacion": (
            r.fecha_creacion.astimezone(zona_arg).isoformat()
            if r.fecha_creacion else None
        ),
        
        # Datos polimórficos normalizados para el frontend
        "objetivo_tipo": objetivo_tipo,
        "objetivo_id": objetivo_id,
        "objetivo_slug": objetivo_slug,
        
        # Datos crudos (por si acaso)
        "id_publicacion": r.id_publicacion,
        "id_comentario": r.id_comentario,
        "id_usuario_reportado": r.id_usuario_reportado
    }

# --- FILTROS ESPECÍFICOS ---

def obtener_reportes_por_publicacion(id_publicacion):
    reportes = (
        Reporte.query.filter_by(id_publicacion=id_publicacion)
        .order_by(Reporte.fecha_creacion.desc()).all()
    )
    return [reporte_to_dict(r) for r in reportes]

def obtener_reportes_por_usuario(id_usuario):
    '''Obtiene reportes hechos POR un usuario (Denunciante).'''
    reportes = (
        Reporte.query.filter_by(id_usuario=id_usuario)
        .order_by(Reporte.fecha_creacion.desc()).all()
    )
    return [reporte_to_dict(r) for r in reportes]

# --- NUEVO: OBTENER REPORTES CONTRA UN USUARIO (Denunciado) ---
def obtener_reportes_contra_usuario(id_usuario_reportado):
    reportes = (
        Reporte.query.filter_by(id_usuario_reportado=id_usuario_reportado)
        .order_by(Reporte.fecha_creacion.desc()).all()
    )
    return [reporte_to_dict(r) for r in reportes]

# --- OTROS ---

def obtener_usuarios_con_posts_reportados():
    '''Obtiene usuarios que tienen publicaciones reportadas.'''
    # (Esta lógica sigue igual porque busca reportes DE PUBLICACIONES)
    publicaciones_reportadas = (
        db.session.query(Publicacion.id, Publicacion.id_usuario)
        .join(Reporte, Reporte.id_publicacion == Publicacion.id)
        .all()
    )

    usuarios_reportados = {}
    for pub_id, user_id in publicaciones_reportadas:
        if user_id not in usuarios_reportados:
            usuarios_reportados[user_id] = []
        usuarios_reportados[user_id].append(pub_id)

    return [
        {"id_usuario": user_id, "publicaciones_reportadas": pubs}
        for user_id, pubs in usuarios_reportados.items()
    ]

def eliminar_reporte(id_reporte):
    reporte = Reporte.query.get(id_reporte)
    if not reporte:
        return {"error": "Reporte no encontrado"}, 404
    db.session.delete(reporte)
    db.session.commit()
    return {"mensaje": "Reporte eliminado"}