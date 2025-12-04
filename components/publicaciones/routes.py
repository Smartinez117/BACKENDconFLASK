from auth.services import require_auth
from flask import Blueprint, request, jsonify, g
from components.publicaciones.services import (
    archivar_publicacion,
    desarchivar_publicacion,
    obtener_publicacion_por_id,
    obtener_publicaciones_filtradas,
    obtener_todas_publicaciones,
    crear_publicacion,
    actualizar_publicacion,
    eliminar_publicacion,
    normalizar_texto,
    obtener_mis_publicaciones,
    subir_imagen_a_cloudinary,
    obtener_publicaciones_para_mapa # IMPORTANTE: Nueva función importada
)

publicaciones_bp = Blueprint("publicaciones", __name__)

# POST
@publicaciones_bp.route("/publicaciones", methods=["POST"])
@require_auth
def crear():
    """Crea una nueva publicación."""
    data = request.get_json()
    data['id_usuario'] = g.usuario_actual.id
    return crear_publicacion(data, g.usuario_actual)

# Obtener una publicación por ID
@publicaciones_bp.route('/publicaciones/<int:id_publicacion>', methods=['GET'])
def get_publicacion(id_publicacion):
    publicacion = obtener_publicacion_por_id(id_publicacion)
    if 'error' in publicacion:
        return jsonify(publicacion), 404
    return jsonify(publicacion), 200

# Obtener todas las publicaciones para el home
@publicaciones_bp.route('/publicaciones', methods=['GET'])
def get_publicaciones():
    page = int(request.args.get("page", 0))
    limit = int(request.args.get("limit", 12))
    offset = page * limit
    publicacion = obtener_todas_publicaciones(offset=offset, limit=limit)
    return jsonify(publicacion), 200

# FILTRAR
@publicaciones_bp.route('/publicaciones/filtrar', methods=['GET'])
def get_publicaciones_filtradas():
    """Endpoint optimizado para filtros."""
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        radio = request.args.get('radio')

        lat = float(lat) if lat else None
        lon = float(lon) if lon else None
        radio = float(radio) if radio else None

        id_categoria = request.args.get('id_categoria') 
        etiquetas = request.args.get('etiquetas')
        fecha_min = request.args.get('fecha_min')
        fecha_max = request.args.get('fecha_max')
        id_usuario = request.args.get('id_usuario')

        page = int(request.args.get("page", 0))
        limit = int(request.args.get("limit", 12))
        offset = page * limit
        
        etiquetas_lista = []
        if etiquetas:
            etiquetas_raw = etiquetas.lower().split(",")
            # Normalizamos aquí para pasarlo limpio al service
            etiquetas_lista = etiquetas_raw # El service ya hace la limpieza interna

        publicaciones = obtener_publicaciones_filtradas(
            lat=lat,
            lon=lon,
            radio_km=radio,
            id_categoria=id_categoria,
            etiquetas=etiquetas_lista,
            fecha_min=fecha_min,
            fecha_max=fecha_max,
            id_usuario=id_usuario,
            offset=offset,
            limit=limit
        )

        return jsonify(publicaciones), 200

    except Exception as error:
        print(f"Error filtrar: {error}")
        return jsonify({'error': str(error)}), 400


# PATCH
@publicaciones_bp.route('/publicaciones/<int:id_publicacion>', methods=['PATCH'])
def actualizar(id_publicacion):
    data = request.get_json()
    try:
        actualizar_publicacion(id_publicacion, data)
        return jsonify({'mensaje': 'Publicación actualizada con éxito'}), 200
    except Exception as error:
        return jsonify({'error': str(error)}), 400

# DELETE
@publicaciones_bp.route('/publicaciones/<int:id_publicacion>', methods=['DELETE'])
def borrar_publicacion(id_publicacion):
    try:
        eliminar_publicacion(id_publicacion)
        return jsonify({'mensaje': 'Publicación eliminada correctamente'}), 200
    except Exception as error:
        return jsonify({'error': str(error)}), 400

@publicaciones_bp.route('/subir-imagenes', methods=['POST'])
def subir_imagenes():
    if 'imagenes' not in request.files:
        return jsonify({"error": "No se encontraron imágenes"}), 400

    archivos = request.files.getlist('imagenes')
    urls = []

    for archivo in archivos:
        url = subir_imagen_a_cloudinary(archivo)
        if url:
            urls.append(url)
        else:
            return jsonify({"error": "Error al subir una imagen"}), 500

    return jsonify({"urls": urls}), 200

# Obtener mis publicaciones
@publicaciones_bp.route("/publicaciones/mis-publicaciones", methods=["GET"])
@require_auth
def publicaciones_usuario_actual():
    usuario = g.usuario_actual
    publicaciones = obtener_mis_publicaciones(usuario.id)
    return jsonify(publicaciones), 200

# Mapa interactivo (OPTIMIZADO)
@publicaciones_bp.route('/publicaciones/mapa', methods=['GET'])
def get_publicaciones_mapa():
    try:
        # Preparamos filtros en un diccionario limpio
        filtros = {
            'lat': float(request.args.get('lat')) if request.args.get('lat') else None,
            'lon': float(request.args.get('lon')) if request.args.get('lon') else None,
            'radio': float(request.args.get('radio')) if request.args.get('radio') else None,
            'id_categoria': request.args.get('id_categoria'),
            'id_usuario': request.args.get('id_usuario'),
            # Si necesitas filtrar por fechas en el mapa también, agrégalos aquí
        }

        # Llamamos a la nueva función optimizada del servicio
        # Ya no hay bucle for ni lógica pesada aquí.
        publicaciones_mapa = obtener_publicaciones_para_mapa(filtros)

        return jsonify(publicaciones_mapa), 200

    except Exception as error:
        print(f"Error Mapa: {error}")
        return jsonify({'error': str(error)}), 400
    
@publicaciones_bp.route('/publicaciones/<int:id_publicacion>/archivar', methods=['PATCH'])
def archivar(id_publicacion):
    try:
        return archivar_publicacion(id_publicacion)
    except Exception as error:
        return jsonify({'error': str(error)}), 400

@publicaciones_bp.route('/publicaciones/<int:id_publicacion>/desarchivar', methods=['PATCH'])
def desarchivar(id_publicacion):
    try:
        return desarchivar_publicacion(id_publicacion)
    except Exception as error:
        return jsonify({'error': str(error)}), 400