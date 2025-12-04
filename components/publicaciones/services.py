import traceback
from flask import jsonify
from components.comentarios.services import eliminar_comentario
from components.imagenes.services import eliminar_imagen
from core.models import Comentario, db, Publicacion, Imagen, Etiqueta, Usuario, Notificacion
from datetime import datetime, timezone
# Nuevos imports necesarios para la optimización SQL
from sqlalchemy import func, cast, Float, desc
from sqlalchemy.orm import joinedload
import unicodedata
import requests

from flask import current_app
import cloudinary
import cloudinary.uploader

import pytz
zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")

# --- NUEVO HELPER DE SERIALIZACIÓN ---
def serializar_publicacion_lista(pub):
    """Convierte una publicación a dict optimizado para listas (Home/Filtros)."""
    # Solo tomamos la primera imagen para la vista de lista
    img_principal = pub.imagenes[0].url if pub.imagenes else None
    
    cat_obj = None
    if pub.categoria_obj:
        cat_obj = {"id": pub.categoria_obj.id, "nombre": pub.categoria_obj.nombre}

    return {
        "id": pub.id,
        "titulo": pub.titulo,
        "localidad": pub.localidad.nombre if pub.localidad else None,
        "categoria": cat_obj,
        "imagenes": [img_principal] if img_principal else [], # Mantenemos formato lista
        "imagen_principal": img_principal, # Extra útil
        "etiquetas": [et.nombre for et in pub.etiquetas],
        "fecha_creacion": pub.fecha_creacion.astimezone(zona_arg).isoformat() if pub.fecha_creacion else None,
        "coordenadas": pub.coordenadas,
        # No enviamos descripción completa para ahorrar datos en listas
    }

# --- FUNCIONES OPTIMIZADAS (LECTURA) ---

def obtener_publicaciones_filtradas(
        lat=None, lon=None, radio_km=None,
        id_categoria=None, etiquetas=None,
        fecha_min=None, fecha_max=None,
        id_usuario=None, offset=0, limit=12
    ):
    """Obtiene publicaciones filtradas aplicando lógica en Base de Datos."""
    try:
        query = db.session.query(Publicacion).filter(
            (Publicacion.estado == 0) | (Publicacion.estado.is_(None))
        )

        # 1. Filtros Básicos
        if id_categoria:
            query = query.filter(Publicacion.id_categoria == id_categoria)
        if id_usuario:
            query = query.filter(Publicacion.id_usuario == id_usuario)
        if fecha_min:
            dt = datetime.strptime(fecha_min, '%Y-%m-%d')
            query = query.filter(Publicacion.fecha_creacion >= dt)
        if fecha_max:
            dt = datetime.strptime(fecha_max, '%Y-%m-%d')
            query = query.filter(Publicacion.fecha_creacion <= dt)

        # 2. Filtro Etiquetas (Optimizado con JOIN)
        if etiquetas:
            etiquetas_norm = [normalizar_texto(e) for e in etiquetas if e.strip()]
            if etiquetas_norm:
                query = query.join(Publicacion.etiquetas).filter(
                    func.lower(Etiqueta.nombre).in_(etiquetas_norm)
                )

        # 3. Filtro Geoespacial (SQL Haversine)
        if lat is not None and lon is not None and radio_km is not None:
            # Asumiendo coordenadas como array/json [lat, lng]
            pub_lat = cast(Publicacion.coordenadas[0], Float)
            pub_lon = cast(Publicacion.coordenadas[1], Float)

            # Fórmula: 6371 * acos(...)
            distancia = 6371 * func.acos(
                func.least(1.0, func.greatest(-1.0, 
                    func.cos(func.radians(lat)) *
                    func.cos(func.radians(pub_lat)) *
                    func.cos(func.radians(pub_lon) - func.radians(lon)) +
                    func.sin(func.radians(lat)) *
                    func.sin(func.radians(pub_lat))
                ))
            )
            query = query.filter(distancia <= radio_km)

        # 4. Carga de relaciones (Eager Loading)
        query = query.options(
            joinedload(Publicacion.imagenes),
            joinedload(Publicacion.localidad),
            joinedload(Publicacion.categoria_obj),
            joinedload(Publicacion.etiquetas)
        )

        # 5. Orden y Paginación (Al final para que sea correcto)
        query = query.order_by(Publicacion.fecha_creacion.desc())
        query = query.offset(offset).limit(limit)
        
        publicaciones = query.all()

        return [serializar_publicacion_lista(pub) for pub in publicaciones]

    except Exception as e:
        print(f"Error filtro: {e}")
        return []

def obtener_todas_publicaciones(offset=0, limit=12):
    """Obtiene todas las publicaciones para el home (Optimizado)."""
    try:
        publicaciones = (
            db.session.query(Publicacion)
            .options(
                joinedload(Publicacion.imagenes),
                joinedload(Publicacion.localidad),
                joinedload(Publicacion.categoria_obj),
                joinedload(Publicacion.etiquetas)
            )
            .filter((Publicacion.estado == 0) | (Publicacion.estado.is_(None)))
            .order_by(Publicacion.fecha_creacion.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [serializar_publicacion_lista(pub) for pub in publicaciones]
    finally:
        # En Flask-SQLAlchemy la sesión suele manejarse sola, 
        # pero si prefieres cerrar explícitamente:
        pass 

def obtener_publicaciones_para_mapa(filtros):
    """
    Query ultra-rápida para el mapa. 
    Solo devuelve lo estrictamente necesario.
    """
    try:
        # Iniciamos query base
        query = db.session.query(Publicacion).filter(
            (Publicacion.estado == 0) | (Publicacion.estado.is_(None))
        )

        # Aplicamos mismos filtros que en el listado
        if filtros.get('id_categoria'):
            query = query.filter(Publicacion.id_categoria == filtros['id_categoria'])
        if filtros.get('id_usuario'):
            query = query.filter(Publicacion.id_usuario == filtros['id_usuario'])
        # ... fechas y etiquetas si fueran necesarias ...

        # Filtro Distancia SQL
        lat = filtros.get('lat')
        lon = filtros.get('lon')
        radio = filtros.get('radio')

        if lat and lon and radio:
            pub_lat = cast(Publicacion.coordenadas[0], Float)
            pub_lon = cast(Publicacion.coordenadas[1], Float)
            distancia = 6371 * func.acos(func.least(1.0, func.greatest(-1.0, 
                func.cos(func.radians(lat)) * func.cos(func.radians(pub_lat)) *
                func.cos(func.radians(pub_lon) - func.radians(lon)) +
                func.sin(func.radians(lat)) * func.sin(func.radians(pub_lat))
            )))
            query = query.filter(distancia <= radio)

        # Cargamos SOLO la categoría y las imágenes para tener la data mínima
        query = query.options(
            joinedload(Publicacion.categoria_obj),
            joinedload(Publicacion.imagenes) 
        )
        
        # Limitamos a 200-500 pines para no saturar el mapa
        resultados = query.limit(200).all()

        mapa_data = []
        for pub in resultados:
            img_principal = pub.imagenes[0].url if pub.imagenes else None
            cat_obj = {"id": pub.categoria_obj.id, "nombre": pub.categoria_obj.nombre} if pub.categoria_obj else None

            mapa_data.append({
                "id": pub.id,
                "titulo": pub.titulo,
                "categoria": cat_obj,
                "coordenadas": pub.coordenadas,
                "imagen_principal": img_principal,
                "descripcion": pub.descripcion # Opcional
            })
            
        return mapa_data

    except Exception as e:
        print(f"Error en mapa backend: {e}")
        return []

# --- MANTENEMOS TUS OTRAS FUNCIONES (CREAR, UPDATE, DELETE, GET_BY_ID) ---

def crear_publicacion(data, usuario):
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
            id_categoria=data.get('id_categoria'),
            descripcion=data.get('descripcion'),
            fecha_creacion=datetime.now(timezone.utc),
            fecha_modificacion=datetime.now(timezone.utc),
            coordenadas=coordenadas
        )

        db.session.add(nueva_publicacion)
        db.session.flush()

        for url in imagenes:
            nueva_imagen = Imagen(id_publicacion=nueva_publicacion.id, url=url)
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
                Usuario.id != usuario.id 
            ).all()
            
            titulo_notif = "Nueva Publicación"
            mensaje_notif = f"Se publicó algo nuevo en tu zona: '{nueva_publicacion.titulo}'."
            for u in usuarios_destino:
                notificacion = Notificacion(
                    id_usuario=u.id,
                    id_publicacion=nueva_publicacion.id,
                    titulo=titulo_notif,
                    descripcion=mensaje_notif,
                    fecha_creacion=datetime.now(timezone.utc),
                    leido=False
                )
                db.session.add(notificacion)

        db.session.commit()
        return {"mensaje": "Publicación creada exitosamente", "id_publicacion": nueva_publicacion.id}, 201

    except Exception as error:
            traceback.print_exc()
            db.session.rollback()
            return {"error": str(error)}, 400

def obtener_publicacion_por_id(id_publicacion):
    pub = Publicacion.query.get(id_publicacion)
    if not pub:
        return {'error': 'Publicación no encontrada'}

    imagenes = Imagen.query.filter_by(id_publicacion=pub.id).all()
    urls_imagenes = [img.url for img in imagenes]
    etiquetas = [et.nombre for et in pub.etiquetas]

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
        'categoria': categoria_data,
        'etiquetas': etiquetas,
        'fecha_creacion': pub.fecha_creacion.astimezone(zona_arg).isoformat() if pub.fecha_creacion else None,
        'fecha_modificacion': pub.fecha_modificacion.astimezone(zona_arg).isoformat() if pub.fecha_modificacion else None,
        'coordenadas': pub.coordenadas,
        'imagenes': urls_imagenes
    }

def actualizar_publicacion(id_publicacion, data):
    publicacion = Publicacion.query.get(id_publicacion)
    if not publicacion:
        raise Exception("Publicación no encontrada")

    publicacion.titulo = data.get('titulo', publicacion.titulo)
    publicacion.descripcion = data.get('descripcion', publicacion.descripcion)
    publicacion.id_categoria = data.get('id_categoria', publicacion.id_categoria)
    publicacion.id_locacion = data.get('id_locacion', publicacion.id_locacion)
    publicacion.coordenadas = data.get('coordenadas', publicacion.coordenadas)
    publicacion.fecha_modificacion = datetime.now(timezone.utc)

    nuevas_imagenes = data.get('imagenes')
    if nuevas_imagenes is not None:
        if len(nuevas_imagenes) > 5:
            raise Exception("No puedes tener más de 5 imágenes por publicación")
        Imagen.query.filter_by(id_publicacion=publicacion.id).delete()
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
    return {"mensaje": "Publicación eliminada correctamente"}

def obtener_info_principal_publicacion(id_publicacion):
    # Se mantiene para otros usos, pero obtener_publicacion_por_id es más completo
    return obtener_publicacion_por_id(id_publicacion)

def obtener_mis_publicaciones(id_usuario):
    publicaciones = (
        db.session.query(Publicacion)
        .options(
            joinedload(Publicacion.imagenes),
            joinedload(Publicacion.categoria_obj)
        )
        .filter(Publicacion.id_usuario == id_usuario)
        .order_by(Publicacion.fecha_creacion.desc())
        .all()
    )
    # Reutilizamos el serializador ligero
    return [serializar_publicacion_lista(pub) for pub in publicaciones]

def obtener_publicaciones_por_usuario(id_usuario):
    return obtener_mis_publicaciones(id_usuario)

def archivar_publicacion(id_publicacion):
    pub = Publicacion.query.get(id_publicacion)
    if not pub: return jsonify({"error": "No encontrada"}), 404
    pub.estado = 1
    pub.fecha_modificacion = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"mensaje": "Archivada"}), 200

def desarchivar_publicacion(id_publicacion):
    pub = Publicacion.query.get(id_publicacion)
    if not pub: return jsonify({"error": "No encontrada"}), 404
    pub.estado = 0
    pub.fecha_modificacion = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"mensaje": "Desarchivada"}), 200

# Helpers
def normalizar_texto(texto):
    if not texto: return ''
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    return texto.lower().strip()

def subir_imagen_a_cloudinary(file):
    try:
        cloudinary.config(
            cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=current_app.config['CLOUDINARY_API_KEY'],
            api_secret=current_app.config['CLOUDINARY_API_SECRET']
        )
        result = cloudinary.uploader.upload(file, upload_preset=current_app.config['CLOUDINARY_UPLOAD_PRESET'])
        return result.get("secure_url")
    except Exception as e:
        print("Error Cloudinary:", str(e))
        return None