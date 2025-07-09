from flask import jsonify
from core.models import db, Publicacion, Imagen
from datetime import datetime
import unicodedata
from core.models import db, Publicacion, Imagen
from datetime import datetime
from math import radians
from sqlalchemy import text


def crear_publicacion(data):
    
    etiquetas_crudas = data.get('etiquetas', '')
    etiquetas_normalizadas = normalizar_texto(etiquetas_crudas)
    
    try:
        nueva_publicacion = Publicacion(
            id_usuario=data.get('id_usuario'),
            id_locacion=data.get('id_locacion'),
            titulo=data.get('titulo'),
            categoria=data.get('categoria'),
            etiquetas= etiquetas_normalizadas,
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
    


def obtener_publicaciones_filtradas(
    lat=None, lon=None, radio_km=None,
    categoria=None, etiquetas=None,
    fecha_min=None, fecha_max=None,
    id_usuario=None
):
    publicaciones = db.session.query(Publicacion)

    if lat is not None and lon is not None and radio_km is not None:
        publicaciones = publicaciones.filter(Publicacion.coordenadas.isnot(None)).all()
    else:
        publicaciones = publicaciones.all()

    resultado = []

    for pub in publicaciones:
        # 🌍 Filtrado por geolocalización
        if lat is not None and lon is not None and radio_km is not None:
            lat_pub, lon_pub = pub.coordenadas
            if calcular_distancia_km(lat, lon, lat_pub, lon_pub) > radio_km:
                continue

        # 📂 Filtrado por categoría
        if categoria and pub.categoria.lower() != categoria.lower():
            continue

        # 🔖 Filtrado por etiquetas
        if etiquetas:
            etiquetas_pub = pub.etiquetas or ""
            etiquetas_pub_normalizadas = normalizar_texto(etiquetas_pub)
            if not all(et in etiquetas_pub_normalizadas for et in etiquetas):
                continue

        # 📅 Filtrado por fechas
        if fecha_min:
            fecha_min_dt = datetime.strptime(fecha_min, '%Y-%m-%d')
            if not pub.fecha_creacion or pub.fecha_creacion < fecha_min_dt:
                continue

        if fecha_max:
            fecha_max_dt = datetime.strptime(fecha_max, '%Y-%m-%d')
            if not pub.fecha_creacion or pub.fecha_creacion > fecha_max_dt:
                continue

        # 🙋‍♂️ Filtrado por usuario
        if id_usuario and str(pub.id_usuario) != str(id_usuario):
            continue

        # 🖼️ Imágenes
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


    
def actualizar_publicacion(id_publicacion, data):
    publicacion = Publicacion.query.get(id_publicacion)

    if not publicacion:
        raise Exception("Publicación no encontrada")
    
    etiquetas_crudas = data.get('etiquetas', '')
    etiquetas_normalizadas = normalizar_texto(etiquetas_crudas)

    # Actualizar campos
    publicacion.titulo = data.get('titulo', publicacion.titulo)
    publicacion.descripcion = data.get('descripcion', publicacion.descripcion)
    publicacion.etiquetas = etiquetas_normalizadas
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
    
    
    
    #Extras
    
def normalizar_texto(texto):
    if not texto:
        return ''
    # Elimina tildes y convierte a minúsculas
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    return texto.lower().strip()


def calcular_distancia_km(lat1, lon1, lat2, lon2):
    # Fórmula de Haversine
    R = 6371  # Radio de la Tierra en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        (pow((radians(lat2 - lat1)) / 2, 2)) +
        (pow((radians(lon2 - lon1)) / 2, 2)) *
        (pow((radians(lat1)), 2))
    )
    c = 2 * R * (a ** 0.5)
    return c