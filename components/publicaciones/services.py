import traceback
from flask import jsonify
from components.comentarios.services import eliminar_comentario
from components.imagenes.services import eliminar_imagen
from core.models import Comentario, db, Publicacion, Imagen, Etiqueta, PublicacionEtiqueta, Categoria,Usuario,Notificacion
from datetime import datetime, timezone
from math import radians, sin, cos, sqrt, atan2
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
    """Crea una nueva publicación con imágenes y etiquetas."""
    try:
        imagenes = data.get('imagenes', [])
        if len(imagenes) > 5:
            return {"error": "No puedes subir más de 5 imágenes por publicación"}, 400
        
        coord = data.get('coordenadas')
        coordenadas = [coord['lat'], coord['lng']] if coord else None

        nueva_publicacion = Publicacion(
            id_usuario= usuario.id,
            id_locacion=data.get('id_locacion'),
            titulo=data.get('titulo'),
            id_categoria=data.get('id_categoria'), # Correcto
            descripcion=data.get('descripcion'),
            fecha_creacion=datetime.now(timezone.utc),
            fecha_modificacion=datetime.now(timezone.utc),
            coordenadas=coordenadas
        )

        db.session.add(nueva_publicacion)
        db.session.flush()

        imagenes = data.get('imagenes', [])
        for url in imagenes:
            nueva_imagen = Imagen(
                id_publicacion=nueva_publicacion.id,
                url=url
            )
            db.session.add(nueva_imagen)

        etiquetas = data.get('etiquetas', [])
        for etiqueta_id in etiquetas:
            etiqueta = Etiqueta.query.get(etiqueta_id)
            if etiqueta:
                nueva_publicacion.etiquetas.append(etiqueta)

        id_loc = data.get('id_locacion')

        if id_loc:
            usuarios_destino = Usuario.query.filter(
                Usuario.id_localidad == id_loc,
                Usuario.id != usuario.id  # excluir al autor
            ).all()

            mensaje_notif = f"Se publicó algo nuevo en tu zona: '{nueva_publicacion.titulo}'."
            titulo_notif = f"Nueva Publicación"

            for u in usuarios_destino:
                notificacion = Notificacion(
                    id_usuario=u.id,
                    id_publicacion = nueva_publicacion.id,
                    titulo = titulo_notif,
                    descripcion=mensaje_notif,
                    fecha_creacion=datetime.now(timezone.utc),
                    leido=False
                )
                db.session.add(notificacion)

        # Commit final
        db.session.commit()

        return {
                "mensaje": "Publicación creada exitosamente",
                "id_publicacion": nueva_publicacion.id
            }, 201

    except Exception as error:
            traceback.print_exc()
            db.session.rollback()
            db.session.close()
            return {"error": str(error)}, 400




def obtener_publicacion_por_id(id_publicacion):
    """Obtiene una publicación por su ID."""
    pub = Publicacion.query.get(id_publicacion)

    if not pub:
        return {'error': 'Publicación no encontrada'}

    imagenes = Imagen.query.filter_by(id_publicacion=pub.id).all()
    urls_imagenes = [img.url for img in imagenes]
    etiquetas = [et.nombre for et in pub.etiquetas]

    # Construir objeto categoría
    categoria_data = None
    if pub.categoria_obj:
        categoria_data = {
            "id": pub.categoria_obj.id,
            "nombre": pub.categoria_obj.nombre
        }

    return {
        'id': pub.id,
        'id_usuario': pub.id_usuario,
        'id_locacion': pub.id_locacion,
        'titulo': pub.titulo,
        'descripcion': pub.descripcion,
        'categoria': categoria_data, # Devolvemos objeto
        'etiquetas': etiquetas,
        'fecha_creacion': (
            pub.fecha_creacion.astimezone(zona_arg).isoformat()
            if pub.fecha_creacion else None
        ),
        'fecha_modificacion': (
            pub.fecha_modificacion.astimezone(zona_arg).isoformat()
            if pub.fecha_modificacion else None
        ),
        'coordenadas': pub.coordenadas,
        'imagenes': urls_imagenes
    }


def obtener_publicaciones_filtradas(
        lat=None,
        lon=None,
        radio_km=None,
        id_categoria=None, # CAMBIO DE NOMBRE PARÁMETRO
        etiquetas=None,
        fecha_min=None,
        fecha_max=None,
        id_usuario=None,
        offset=0,
        limit=12
    ):
    """Obtiene publicaciones filtradas."""
    query = db.session.query(Publicacion).options(
        joinedload(Publicacion.imagenes),
        joinedload(Publicacion.etiquetas),
        joinedload(Publicacion.localidad),
        joinedload(Publicacion.categoria_obj) # Cargamos relación categoria
    )
    query = query.filter((Publicacion.estado == 0) | (Publicacion.estado.is_(None)))

    # FILTRO POR ID DE CATEGORÍA
    if id_categoria:
        query = query.filter(Publicacion.id_categoria == id_categoria)

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
            for etiqueta in etiquetas_normalizadas:
                query = query.filter(
                    Publicacion.etiquetas.any(func.lower(Etiqueta.nombre) == etiqueta)
                )
        else:
            return []

    if lat is not None and lon is not None and radio_km is not None:
        query = query.filter(Publicacion.coordenadas.isnot(None))

    query = query.order_by(Publicacion.fecha_creacion.desc())
    query = query.offset(offset).limit(limit)
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
        
        # Construir objeto categoría seguro
        cat_obj = None
        if pub.categoria_obj:
            cat_obj = {
                "id": pub.categoria_obj.id,
                "nombre": pub.categoria_obj.nombre
            }

        resultado.append({
            "id": pub.id,
            "titulo": pub.titulo,
            "localidad": pub.localidad.nombre if pub.localidad else None,
            "categoria": cat_obj, # AQUÍ ESTABA EL ERROR
            "imagenes": urls_imagenes,
            "etiquetas": etiquetas,
            "fecha_creacion": (
                pub.fecha_creacion.astimezone(zona_arg).isoformat()
                if pub.fecha_creacion else None
            ),
            "coordenadas": pub.coordenadas,
            "descripcion": pub.descripcion
        })

    return resultado


def obtener_todas_publicaciones(offset=0, limit=12):
    """Obtiene todas las publicaciones ordenadas por fecha."""
    try:
        publicaciones = (
            db.session.query(Publicacion)
            .options(
                joinedload(Publicacion.imagenes),
                joinedload(Publicacion.etiquetas),
                joinedload(Publicacion.localidad),
                joinedload(Publicacion.categoria_obj) # IMPORTANTE: cargar categoria
            )
            .order_by(Publicacion.fecha_creacion.desc())
            .filter((Publicacion.estado == 0) | (Publicacion.estado.is_(None)))
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        resultado = []
        for pub in publicaciones:
            primer_imagen = pub.imagenes[0].url if pub.imagenes else None
            etiquetas = [et.nombre for et in pub.etiquetas]
            
            # Construir objeto categoría seguro
            cat_obj = None
            if pub.categoria_obj:
                cat_obj = {
                    "id": pub.categoria_obj.id,
                    "nombre": pub.categoria_obj.nombre
                }

            resultado.append({
                "id": pub.id,
                "titulo": pub.titulo,
                "localidad": pub.localidad.nombre if pub.localidad else None,
                "categoria": cat_obj, # AQUÍ ESTABA EL ERROR PRINCIPAL
                "imagenes": primer_imagen,
                "etiquetas": etiquetas,
                "fecha_creacion": (
                    pub.fecha_creacion.astimezone(zona_arg).isoformat()
                    if pub.fecha_creacion else None
                ),
            })

        return resultado

    finally:
        db.session.remove()


def actualizar_publicacion(id_publicacion, data):
    """Actualiza los datos de una publicación existente."""
    publicacion = Publicacion.query.get(id_publicacion)
    if not publicacion:
        raise Exception("Publicación no encontrada")

    # Actualizar campos básicos
    publicacion.titulo = data.get('titulo', publicacion.titulo)
    publicacion.descripcion = data.get('descripcion', publicacion.descripcion)
    
    # CORREGIDO: usar id_categoria
    publicacion.id_categoria = data.get('id_categoria', publicacion.id_categoria)
    
    publicacion.id_locacion = data.get('id_locacion', publicacion.id_locacion)
    publicacion.coordenadas = data.get('coordenadas', publicacion.coordenadas)
    publicacion.fecha_modificacion = datetime.now(timezone.utc)

    nuevas_imagenes = data.get('imagenes')
    if nuevas_imagenes is not None:
        # 1. Validar cantidad
        if len(nuevas_imagenes) > 5:
            raise Exception("No puedes tener más de 5 imágenes por publicación")

        # 2. Borrar anteriores (Lógica de reemplazo completo)
        Imagen.query.filter_by(id_publicacion=publicacion.id).delete()
        
        # 3. Insertar nuevas
        for url in nuevas_imagenes:
            nueva_imagen = Imagen(id_publicacion=publicacion.id, url=url)
            db.session.add(nueva_imagen)

    nuevas_etiquetas_ids = data.get('etiquetas', [])
    if nuevas_etiquetas_ids is not None:
        etiquetas = Etiqueta.query.filter(Etiqueta.id.in_(nuevas_etiquetas_ids)).all()
        publicacion.etiquetas = etiquetas

    db.session.commit()


def eliminar_publicacion(id_publicacion):
    publicacion = Publicacion.query.get(id_publicacion)
    if not publicacion:
        raise Exception("Publicación no encontrada")

    for comentario in Comentario.query.filter_by(id_publicacion=publicacion.id).all():
        eliminar_comentario(comentario.id)

    for img in Imagen.query.filter_by(id_publicacion=publicacion.id).all():
        eliminar_imagen(img.id)

    db.session.delete(publicacion)
    db.session.commit()


# Extras (normalizar_texto, calcular_distancia_km, subir_imagen... iguales)
def normalizar_texto(texto):
    if not texto:
        return ''
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    return texto.lower().strip()

def calcular_distancia_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def subir_imagen_a_cloudinary(file):
    try:
        cloudinary.config(
            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=current_app.config['CLOUDINARY_API_KEY'],
            api_secret=current_app.config['CLOUDINARY_API_SECRET']
        )
        result = cloudinary.uploader.upload(
            file,
            upload_preset=current_app.config['CLOUDINARY_UPLOAD_PRESET']
        )
        return result.get("secure_url")
    except Exception as e:
        print("Error al subir imagen:", str(e))
        return None


def obtener_info_principal_publicacion(id_publicacion):
    pub = Publicacion.query.get(id_publicacion)
    if not pub:
        return {'error': 'Publicación no encontrada'}

    imagen_principal = pub.imagenes[0].url if pub.imagenes else None
    
    cat_obj = None
    if pub.categoria_obj:
        cat_obj = {
            "id": pub.categoria_obj.id,
            "nombre": pub.categoria_obj.nombre
        }

    return {
        'id': pub.id,
        'titulo': pub.titulo,
        'descripcion': pub.descripcion,
        'categoria': cat_obj, # CORREGIDO
        'coordenadas': pub.coordenadas,
        'imagen_principal': imagen_principal
    }

def obtener_publicaciones_por_usuario(id_usuario):
    # 1. Hacemos la query optimizada (eager loading)
    publicaciones = (
        db.session.query(Publicacion)
        .options(
            joinedload(Publicacion.imagenes),
            joinedload(Publicacion.etiquetas),
            joinedload(Publicacion.localidad),
            joinedload(Publicacion.categoria_obj) # IMPORTANTE: Cargar la relación
        )
        .filter(Publicacion.id_usuario == id_usuario)
        .order_by(Publicacion.fecha_creacion.desc())
        .all()
    )

    # 2. Usamos la lógica que YA escribiste en el modelo.
    # Esto devuelve la lista de diccionarios con la categoría como objeto.
    return [pub.to_dict() for pub in publicaciones]

def archivar_publicacion(id_publicacion):
    pub = Publicacion.query.get(id_publicacion)
    if not pub:
        return jsonify({"error": "Publicación no encontrada"}), 404
    
    pub.estado = 1
    pub.fecha_modificacion = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"mensaje": "Publicación archivada"}), 200

def desarchivar_publicacion(id_publicacion):
    pub = Publicacion.query.get(id_publicacion)
    if not pub:
        return jsonify({"error": "Publicación no encontrada"}), 404
    
    pub.estado = 0
    pub.fecha_modificacion = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"mensaje": "Publicación archivada"}), 200