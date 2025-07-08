from flask import jsonify
from core.models import db, Publicacion, Imagen
from datetime import datetime

from core.models import db, Publicacion, Imagen
from datetime import datetime

def crear_publicacion(data):
    try:
        nueva_publicacion = Publicacion(
            id_usuario=data.get('id_usuario'),
            id_locacion=data.get('id_locacion'),
            titulo=data.get('titulo'),
            categoria=data.get('categoria'),
            etiquetas=data.get('etiquetas'),
            descripcion=data.get('descripcion'),
            fecha_creacion=datetime.utcnow(),
            fecha_modificacion=datetime.utcnow(),
            coordenadas=data.get('coordenadas')  # esto debe ser una lista [lat, long]
        )

        db.session.add(nueva_publicacion)
        db.session.flush()  # obtener el ID generado sin hacer commit todavía

        # Agregar imágenes si existen
        imagenes = data.get('imagenes', [])
        for url in imagenes:
            nueva_imagen = Imagen(
                id_publicacion=nueva_publicacion.id,
                url=url
            )
            db.session.add(nueva_imagen)

        db.session.commit()

        return {
            "mensaje": "Publicación creada exitosamente",
            "id_publicacion": nueva_publicacion.id
        }, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400
    


def obtener_todas_las_publicaciones():
    publicaciones = Publicacion.query.all()
    resultado = []

    for pub in publicaciones:
        imagenes = Imagen.query.filter_by(id_publicacion=pub.id).all()
        urls_imagenes = [img.url for img in imagenes]

        resultado.append({
            'id': pub.id,
            'id_usuario': pub.id_usuario,
            'id_locacion': pub.id_locacion,
            'titulo': pub.titulo,
            'descripcion': pub.descripcion,
            'etiquetas': pub.etiquetas,
            'categoria': pub.categoria,
            'fecha_creacion': pub.fecha_creacion.isoformat() if pub.fecha_creacion else None,
            'fecha_modificacion': pub.fecha_modificacion.isoformat() if pub.fecha_modificacion else None,
            'coordenadas': pub.coordenadas,
            'imagenes': urls_imagenes
        })

    return resultado

def obtener_publicaciones_por_categoria(categoria):
    publicaciones = Publicacion.query.filter_by(categoria=categoria).all()
    resultado = []

    for pub in publicaciones:
        imagenes = Imagen.query.filter_by(id_publicacion=pub.id).all()
        urls_imagenes = [img.url for img in imagenes]

        resultado.append({
            'id': pub.id,
            'id_usuario': pub.id_usuario,
            'id_locacion': pub.id_locacion,
            'titulo': pub.titulo,
            'descripcion': pub.descripcion,
            'etiquetas': pub.etiquetas,
            'categoria': pub.categoria,
            'fecha_creacion': pub.fecha_creacion.isoformat() if pub.fecha_creacion else None,
            'fecha_modificacion': pub.fecha_modificacion.isoformat() if pub.fecha_modificacion else None,
            'coordenadas': pub.coordenadas,
            'imagenes': urls_imagenes
        })

    return resultado


def obtener_publicacion_por_id(id_publicacion):
    pub = Publicacion.query.get(id_publicacion)

    if not pub:
        return {'error': 'Publicación no encontrada'}

    imagenes = Imagen.query.filter_by(id_publicacion=pub.id).all()
    urls_imagenes = [img.url for img in imagenes]

    return {
        'id': pub.id,
            'id_usuario': pub.id_usuario,
            'id_locacion': pub.id_locacion,
            'titulo': pub.titulo,
            'descripcion': pub.descripcion,
            'etiquetas': pub.etiquetas,
            'categoria': pub.categoria,
            'fecha_creacion': pub.fecha_creacion.isoformat() if pub.fecha_creacion else None,
            'fecha_modificacion': pub.fecha_modificacion.isoformat() if pub.fecha_modificacion else None,
            'coordenadas': pub.coordenadas,
            'imagenes': urls_imagenes
    }
    
    
    
def actualizar_publicacion(id_publicacion, data):
    publicacion = Publicacion.query.get(id_publicacion)

    if not publicacion:
        raise Exception("Publicación no encontrada")

    # Actualizar campos
    publicacion.titulo = data.get('titulo', publicacion.titulo)
    publicacion.descripcion = data.get('descripcion', publicacion.descripcion)
    publicacion.etiquetas = data.get('etiquetas', publicacion.etiquetas)
    publicacion.categoria = data.get('categoria', publicacion.categoria)
    publicacion.id_locacion = data.get('id_locacion', publicacion.id_locacion)
    publicacion.coordenadas = data.get('coordenadas', publicacion.coordenadas)
    publicacion.fecha_modificacion = datetime.utcnow()

    # Actualizar imágenes si se envían nuevas
    nuevas_imagenes = data.get('imagenes')
    if nuevas_imagenes is not None:
        # Eliminar imágenes anteriores
        Imagen.query.filter_by(id_publicacion=publicacion.id).delete()

        # Agregar nuevas imágenes
        for url in nuevas_imagenes:
            nueva_imagen = Imagen(id_publicacion=publicacion.id, url=url)
            db.session.add(nueva_imagen)

    db.session.commit()
    
    
    
def eliminar_publicacion(id_publicacion):
    publicacion = Publicacion.query.get(id_publicacion)

    if not publicacion:
        raise Exception("Publicación no encontrada")

    # Eliminar imágenes asociadas
    Imagen.query.filter_by(id_publicacion=publicacion.id).delete()

    # Eliminar la publicación
    db.session.delete(publicacion)
    db.session.commit()