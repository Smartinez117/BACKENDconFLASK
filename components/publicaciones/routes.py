from auth.services import require_auth
from flask import Blueprint, request, jsonify, g
from components.publicaciones.services import (
    archivar_publicacion,
    desarchivar_publicacion,
    obtener_publicacion_por_id,
    obtener_publicaciones_filtradas,
    obtener_publicaciones_por_usuario,
    obtener_todas_publicaciones,
    crear_publicacion,
    actualizar_publicacion,
    eliminar_publicacion,
    normalizar_texto,
    obtener_info_principal_publicacion,
)
from components.publicaciones.services import subir_imagen_a_cloudinary

publicaciones_bp = Blueprint("publicaciones", __name__)

# POST
@publicaciones_bp.route("/publicaciones", methods=["POST"])
@require_auth
def crear():
    """Crea una nueva publicación con los datos recibidos y el usuario autenticado."""
    data = request.get_json()
    data['id_usuario'] = g.usuario_actual.id
    return crear_publicacion(data, g.usuario_actual)

# Obtener una publicación por ID
@publicaciones_bp.route('/publicaciones/<int:id_publicacion>', methods=['GET'])
def get_publicacion(id_publicacion):
    """Obtiene una publicación por su ID."""
    publicacion = obtener_publicacion_por_id(id_publicacion)
    return jsonify(publicacion), 200

# Obtener todas las publicaciones para el home
@publicaciones_bp.route('/publicaciones', methods=['GET'])
def get_publicaciones():
    """Obtiene todas las publicaciones para el home."""
    page = int(request.args.get("page", 0))
    limit = int(request.args.get("limit", 12))
    offset = page * limit
    publicacion = obtener_todas_publicaciones(offset=offset, limit=limit)
    return jsonify(publicacion), 200


# FILTRAR (CORREGIDO)
@publicaciones_bp.route('/publicaciones/filtrar', methods=['GET'])
def get_publicaciones_filtradas():
    """Obtiene publicaciones filtradas por ubicación, categoría, etiquetas, fechas o usuario."""
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        radio = request.args.get('radio')

        lat = float(lat) if lat else None
        lon = float(lon) if lon else None
        radio = float(radio) if radio else None

        # --- CAMBIO: Ahora recibimos id_categoria ---
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
            etiquetas_lista = [normalizar_texto(e) for e in etiquetas_raw]

        publicaciones = obtener_publicaciones_filtradas(
            lat=lat,
            lon=lon,
            radio_km=radio,
            id_categoria=id_categoria, # Pasamos el ID
            etiquetas=etiquetas_lista,
            fecha_min=fecha_min,
            fecha_max=fecha_max,
            id_usuario=id_usuario,
            offset=offset,
            limit=limit
        )

        return jsonify(publicaciones), 200

    except Exception as error:
        print(error) # Log para ver errores en consola backend
        return jsonify({'error': str(error)}), 400


# PATCH
@publicaciones_bp.route('/publicaciones/<int:id_publicacion>', methods=['PATCH'])
def actualizar(id_publicacion):
    """Actualiza una publicación existente por su ID."""
    data = request.get_json()
    try:
        actualizar_publicacion(id_publicacion, data)
        return jsonify({'mensaje': 'Publicación actualizada con éxito'}), 200
    except Exception as error:
        return jsonify({'error': str(error)}), 400

# DELETE
@publicaciones_bp.route('/publicaciones/<int:id_publicacion>', methods=['DELETE'])
def borrar_publicacion(id_publicacion):
    """Elimina una publicación por su ID."""
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


# Obtener publicaciones por usuario
@publicaciones_bp.route("/publicaciones/mis-publicaciones", methods=["GET"])
@require_auth
def publicaciones_usuario_actual():
    """Obtiene todas las publicaciones del usuario autenticado."""
    usuario = g.usuario_actual
    publicaciones = obtener_publicaciones_por_usuario(usuario.id)
    return jsonify(publicaciones), 200


# Mapa interactivo
@publicaciones_bp.route('/publicaciones/mapa', methods=['GET'])
def get_publicaciones_mapa():
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        radio = request.args.get('radio')

        lat = float(lat) if lat else None
        lon = float(lon) if lon else None
        radio = float(radio) if radio else None

        id_categoria = request.args.get('id_categoria') # CORREGIDO
        etiquetas = request.args.get('etiquetas')
        fecha_min = request.args.get('fecha_min')
        fecha_max = request.args.get('fecha_max')
        id_usuario = request.args.get('id_usuario')

        etiquetas_lista = []
        if etiquetas:
            etiquetas_raw = etiquetas.lower().split(",")
            etiquetas_lista = [normalizar_texto(e) for e in etiquetas_raw]

        publicaciones = obtener_publicaciones_filtradas(
            lat=lat,
            lon=lon,
            radio_km=radio,
            id_categoria=id_categoria, # CORREGIDO
            etiquetas=etiquetas_lista,
            fecha_min=fecha_min,
            fecha_max=fecha_max,
            id_usuario=id_usuario
        )

        publicaciones_mapa = []
        for pub in publicaciones:
            # Como obtener_publicaciones_filtradas ahora devuelve diccionarios (por la corrección abajo),
            # podemos usarlos directamente o extraer lo necesario.
            # OJO: obtener_publicaciones_filtradas ya devuelve una lista de dicts, no objetos.
            
            publicaciones_mapa.append({
                "id": pub["id"],
                "titulo": pub["titulo"],
                "categoria": pub["categoria"], # Esto ahora será un objeto {id, nombre}
                "coordenadas": obtener_info_principal_publicacion(pub["id"])["coordenadas"], # Re-query rápido para coords crudas si no vienen en el dict
                "imagen_principal": pub["imagenes"][0] if pub["imagenes"] else None
            })

        return jsonify(publicaciones_mapa), 200

    except Exception as error:
        return jsonify({'error': str(error)}), 400

@publicaciones_bp.route('/publicaciones/<int:id_publicacion>/archivar', methods=['PATCH'])
def archivar(id_publicacion):
    try:
        archivar_publicacion(id_publicacion)
        return jsonify({"mensaje": "Publicación archivada"}), 200
    except Exception as error:
        return jsonify({'error': str(error)}), 400

@publicaciones_bp.route('/publicaciones/<int:id_publicacion>/desarchivar', methods=['PATCH'])
def desarchivar(id_publicacion):
    try:
        desarchivar_publicacion(id_publicacion)
        return jsonify({"mensaje": "Publicación desarchivada"}), 200
    except Exception as error:
        return jsonify({'error': str(error)}), 400