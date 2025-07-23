from flask import jsonify
from comentarios.services import eliminar_comentario
from imagenes.services import eliminar_imagen
from core.models import Comentario, db, Publicacion, Imagen, Etiqueta, PublicacionEtiqueta
from datetime import datetime
from math import radians
from sqlalchemy import text, func
import unicodedata


def crear_publicacion(data):
    try:
        nueva_publicacion = Publicacion(
            id_usuario=data.get('id_usuario'),
            id_locacion=data.get('id_locacion'),
            titulo=data.get('titulo'),
            categoria=data.get('categoria'),
            descripcion=data.get('descripcion'),
            fecha_creacion=datetime.utcnow(),
            fecha_modificacion=datetime.utcnow(),
            coordenadas=data.get('coordenadas')  # lista [lat, lon]
        )

        db.session.add(nueva_publicacion)
        db.session.flush()  # obtener ID generado

        # Imágenes
        imagenes = data.get('imagenes', [])
        for url in imagenes:
            nueva_imagen = Imagen(
                id_publicacion=nueva_publicacion.id,
                url=url
            )
            db.session.add(nueva_imagen)

        # Etiquetas
        etiquetas = data.get('etiquetas', [])
        for etiqueta_texto in etiquetas:
            etiqueta_normalizada = normalizar_texto(etiqueta_texto)
            etiqueta = Etiqueta.query.filter(func.lower(Etiqueta.nombre) == etiqueta_normalizada).first()
            if not etiqueta:
                etiqueta = Etiqueta(nombre=etiqueta_normalizada)
                db.session.add(etiqueta)
                db.session.flush()  # obtener id

            nueva_publicacion.etiquetas.append(etiqueta)

        db.session.commit()

        return {
            "mensaje": "Publicación creada exitosamente",
            "id_publicacion": nueva_publicacion.id
        }, 201

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 400


def obtener_publicacion_por_id(id_publicacion):
    pub = Publicacion.query.get(id_publicacion)

    if not pub:
        return {'error': 'Publicación no encontrada'}

    imagenes = Imagen.query.filter_by(id_publicacion=pub.id).all()
    urls_imagenes = [img.url for img in imagenes]
    etiquetas = [et.nombre for et in pub.etiquetas]

    return {
        'id': pub.id,
        'id_usuario': pub.id_usuario,
        'id_locacion': pub.id_locacion,
        'titulo': pub.titulo,
        'descripcion': pub.descripcion,
        'categoria': pub.categoria,
        'etiquetas': etiquetas,
        'fecha_creacion': pub.fecha_creacion.isoformat() if pub.fecha_creacion else None,
        'fecha_modificacion': pub.fecha_modificacion.isoformat() if pub.fecha_modificacion else None,
        'coordenadas': pub.coordenadas,
        'imagenes': urls_imagenes
    }


def obtener_publicaciones_filtradas(lat=None, lon=None, radio_km=None, categoria=None, etiquetas=None, fecha_min=None, fecha_max=None, id_usuario=None):
    query = db.session.query(Publicacion)

    if categoria:
        query = query.filter(func.lower(Publicacion.categoria) == categoria.lower())

    if id_usuario:
        query = query.filter(Publicacion.id_usuario == id_usuario)

    if fecha_min:
        fecha_min_dt = datetime.strptime(fecha_min, '%Y-%m-%d')
        query = query.filter(Publicacion.fecha_creacion >= fecha_min_dt)

    if fecha_max:
        fecha_max_dt = datetime.strptime(fecha_max, '%Y-%m-%d')
        query = query.filter(Publicacion.fecha_creacion <= fecha_max_dt)

    if etiquetas:
        etiquetas_normalizadas = [normalizar_texto(e) for e in etiquetas if normalizar_texto(e).strip()]
        if etiquetas_normalizadas:
            for et in etiquetas_normalizadas:
                query = query.filter(
                    Publicacion.etiquetas.any(func.lower(Etiqueta.nombre) == et)
                )
        else:
            return []

    if lat is not None and lon is not None and radio_km is not None:
        query = query.filter(Publicacion.coordenadas.isnot(None))

    publicaciones = query.all()

    if lat is not None and lon is not None and radio_km is not None:
        publicaciones = [
            pub for pub in publicaciones
            if calcular_distancia_km(lat, lon, *pub.coordenadas) <= radio_km
        ]

    resultado = []
    for pub in publicaciones:
        imagenes = Imagen.query.filter_by(id_publicacion=pub.id).all()
        urls_imagenes = [img.url for img in imagenes]
        etiquetas = [et.nombre for et in pub.etiquetas]

        resultado.append({
            'id': pub.id,
            'id_usuario': pub.id_usuario,
            'id_locacion': pub.id_locacion,
            'titulo': pub.titulo,
            'descripcion': pub.descripcion,
            'categoria': pub.categoria,
            'etiquetas': etiquetas,
            'fecha_creacion': pub.fecha_creacion.isoformat() if pub.fecha_creacion else None,
            'fecha_modificacion': pub.fecha_modificacion.isoformat() if pub.fecha_modificacion else None,
            'coordenadas': pub.coordenadas,
            'imagenes': urls_imagenes
        })

    return resultado


def actualizar_publicacion(id_publicacion, data):
    publicacion = Publicacion.query.get(id_publicacion)

    if not publicacion:
        raise Exception("Publicación no encontrada")

    # Actualizar campos
    publicacion.titulo = data.get('titulo', publicacion.titulo)
    publicacion.descripcion = data.get('descripcion', publicacion.descripcion)
    publicacion.categoria = data.get('categoria', publicacion.categoria)
    publicacion.id_locacion = data.get('id_locacion', publicacion.id_locacion)
    publicacion.coordenadas = data.get('coordenadas', publicacion.coordenadas)
    publicacion.fecha_modificacion = datetime.utcnow()

    # Actualizar imágenes
    nuevas_imagenes = data.get('imagenes')
    if nuevas_imagenes is not None:
        Imagen.query.filter_by(id_publicacion=publicacion.id).delete()
        for url in nuevas_imagenes:
            nueva_imagen = Imagen(id_publicacion=publicacion.id, url=url)
            db.session.add(nueva_imagen)

    # Actualizar etiquetas
    nuevas_etiquetas = data.get('etiquetas', [])
    publicacion.etiquetas.clear()  # Elimina todas
    for etiqueta_texto in nuevas_etiquetas:
        etiqueta_normalizada = normalizar_texto(etiqueta_texto)
        etiqueta = Etiqueta.query.filter(func.lower(Etiqueta.nombre) == etiqueta_normalizada).first()
        if not etiqueta:
            etiqueta = Etiqueta(nombre=etiqueta_normalizada)
            db.session.add(etiqueta)
            db.session.flush()
        publicacion.etiquetas.append(etiqueta)

    db.session.commit()


def eliminar_publicacion(id_publicacion):
    publicacion = Publicacion.query.get(id_publicacion)

    if not publicacion:
        raise Exception("Publicación no encontrada")

    for c in Comentario.query.filter_by(id_publicacion=publicacion.id).all():
        eliminar_comentario(c.id)

    for img in Imagen.query.filter_by(id_publicacion=publicacion.id).all():
        eliminar_imagen(img.id)

    db.session.delete(publicacion)
    db.session.commit()


# Extras

def normalizar_texto(texto):
    if not texto:
        return ''
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    return texto.lower().strip()


def calcular_distancia_km(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2

    R = 6371  # km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c
