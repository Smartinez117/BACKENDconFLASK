from flask import jsonify
from components.comentarios.services import eliminar_comentario
from components.imagenes.services import eliminar_imagen
from core.models import Comentario, db, Publicacion, Imagen, Etiqueta, PublicacionEtiqueta
from datetime import datetime, timezone
from math import radians
from sqlalchemy import text, func
from sqlalchemy.orm import joinedload
import unicodedata
import requests

from flask import current_app
import cloudinary
import cloudinary.uploader

import pytz
zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")


def crear_publicacion(data, usuario):
    try:
        # Obtener coordenadas como lista [lat, lng]
        coord = data.get('coordenadas')  # ← esto es el objeto que llega del frontend
        coordenadas = [coord['lat'], coord['lng']] if coord else None

        nueva_publicacion = Publicacion(
            id_usuario= usuario.id,
            id_locacion=data.get('id_locacion'),
            titulo=data.get('titulo'),
            categoria=data.get('categoria'),
            descripcion=data.get('descripcion'),
            fecha_creacion=datetime.now(timezone.utc),
            fecha_modificacion=datetime.now(timezone.utc),
            coordenadas=coordenadas
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
        for etiqueta_id in etiquetas:
            etiqueta = Etiqueta.query.get(etiqueta_id)
            if etiqueta:
                nueva_publicacion.etiquetas.append(etiqueta)


        db.session.commit()

        return {
            "mensaje": "Publicación creada exitosamente",
            "id_publicacion": nueva_publicacion.id
        }, 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        db.session.close()
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
        'fecha_creacion': pub.fecha_creacion.astimezone(zona_arg).isoformat() if pub.fecha_creacion else None,
        'fecha_modificacion': pub.fecha_modificacion.astimezone(zona_arg).isoformat() if pub.fecha_modificacion else None,
        'coordenadas': pub.coordenadas,
        'imagenes': urls_imagenes
    }


def obtener_publicaciones_filtradas(lat=None, lon=None, radio_km=None, categoria=None, etiquetas=None, fecha_min=None, fecha_max=None, id_usuario=None):
    query = db.session.query(Publicacion).options(
        joinedload(Publicacion.imagenes),  #left join de imagenes y etiquetas
        joinedload(Publicacion.etiquetas),
        joinedload(Publicacion.localidad)
    )
    

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


    query = query.order_by(Publicacion.fecha_creacion.desc())
    publicaciones = query.all()

    if lat is not None and lon is not None and radio_km is not None:
        publicaciones = [
            pub for pub in publicaciones
            if calcular_distancia_km(lat, lon, *pub.coordenadas) <= radio_km
        ]

    resultado = []
    for pub in publicaciones:
        urls_imagenes = [img.url for img in pub.imagenes]
        etiquetas = [et.nombre for et in pub.etiquetas]

        resultado.append({
                "id": pub.id,
                "titulo": pub.titulo,
                "localidad": pub.localidad.nombre if pub.localidad else None,  # traemos el nombre
                "categoria": pub.categoria,
                "imagenes": urls_imagenes,
                "etiquetas": etiquetas
            })

    return resultado


def obtener_todas_publicaciones():
    try:
        publicaciones = (
            db.session.query(Publicacion)
            .options(
                joinedload(Publicacion.imagenes),
                joinedload(Publicacion.etiquetas),
                joinedload(Publicacion.localidad)  # cargamos la relación Localidad
            )
            .order_by(Publicacion.fecha_creacion.desc())
            .all()
        )

        resultado = []
        for pub in publicaciones:
            primer_imagen = pub.imagenes[0].url if pub.imagenes else None
            etiquetas = [et.nombre for et in pub.etiquetas]

            resultado.append({
                "id": pub.id,
                "titulo": pub.titulo,
                "localidad": pub.localidad.nombre if pub.localidad else None,  # traemos el nombre
                "categoria": pub.categoria,
                "imagenes": primer_imagen,
                "etiquetas": etiquetas
            })

        return resultado

    finally:
        db.session.remove()


def actualizar_publicacion(id_publicacion, data):
    publicacion = Publicacion.query.get(id_publicacion)
    if not publicacion:
        raise Exception("Publicación no encontrada")

    # Actualizar campos básicos
    publicacion.titulo = data.get('titulo', publicacion.titulo)
    publicacion.descripcion = data.get('descripcion', publicacion.descripcion)
    publicacion.categoria = data.get('categoria', publicacion.categoria)
    publicacion.id_locacion = data.get('id_locacion', publicacion.id_locacion)
    publicacion.coordenadas = data.get('coordenadas', publicacion.coordenadas)
    publicacion.fecha_modificacion = datetime.now(timezone.utc)

    # Actualizar imágenes
    nuevas_imagenes = data.get('imagenes')
    if nuevas_imagenes is not None:
        Imagen.query.filter_by(id_publicacion=publicacion.id).delete()
        for url in nuevas_imagenes:
            nueva_imagen = Imagen(id_publicacion=publicacion.id, url=url)
            db.session.add(nueva_imagen)

    # Actualizar etiquetas por ID
    nuevas_etiquetas_ids = data.get('etiquetas', [])
    if nuevas_etiquetas_ids:
        etiquetas = Etiqueta.query.filter(Etiqueta.id.in_(nuevas_etiquetas_ids)).all()
        publicacion.etiquetas = etiquetas  # reemplaza directamente

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

#Para subir imagenes a cloudinary

#def subir_imagen_a_cloudinary(file):
   # url = "https://api.cloudinary.com/v1_1/redema/image/upload"
    
    #data = {
     #   "upload_preset": "redema_imagenes"
    #}

    #files = {
    #    "file": file
    #}

    #response = requests.post(url, data=data, files=files)
    
    #if response.status_code == 200:
     #   return response.json().get("secure_url")
    #else:
     #   print("Error al subir la imagen:", response.text)
      #  return None

def subir_imagen_a_cloudinary(file):
    try:
        # Configura Cloudinary con los valores desde app.config
        cloudinary.config(
            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=current_app.config['CLOUDINARY_API_KEY'],
            api_secret=current_app.config['CLOUDINARY_API_SECRET']
        )

        # Sube la imagen
        result = cloudinary.uploader.upload(
            file,
            upload_preset=current_app.config['CLOUDINARY_UPLOAD_PRESET']
        )

        return result.get("secure_url")

    except Exception as e:
        print("Error al subir imagen:", str(e))
        return None
