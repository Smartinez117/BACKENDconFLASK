from flask import Blueprint, request, jsonify
from publicaciones.services import (
    obtener_todas_las_publicaciones,
    obtener_publicaciones_por_categoria,
    obtener_publicacion_por_id,
    obtener_publicaciones_por_etiquetas,
    crear_publicacion,
    actualizar_publicacion,
    eliminar_publicacion,
    normalizar_texto
)
publicaciones_bp = Blueprint("publicaciones", __name__)

# POST
@publicaciones_bp.route("/publicaciones", methods=["POST"])
def crear():
    data = request.get_json()
    return crear_publicacion(data)



@publicaciones_bp.route('/publicaciones', methods=['GET'])
def get_all_publicaciones():
    publicaciones = obtener_todas_las_publicaciones()
    return jsonify(publicaciones), 200

# Obtener publicaciones por categoría
@publicaciones_bp.route('/publicaciones/categoria/<string:categoria>', methods=['GET'])
def get_publicaciones_por_categoria(categoria):
    publicaciones = obtener_publicaciones_por_categoria(categoria)
    return jsonify(publicaciones), 200

# Obtener una publicación por ID
@publicaciones_bp.route('/publicaciones/<int:id_publicacion>', methods=['GET'])
def get_publicacion(id_publicacion):
    publicacion = obtener_publicacion_por_id(id_publicacion)
    return jsonify(publicacion), 200

# Obtener una publicación por etiquetas (Filtrado) GET /publicaciones/etiquetas?etiquetas=perro,negro,callejero
@publicaciones_bp.route('/publicaciones/etiquetas', methods=['GET'])
def get_publicaciones_por_etiquetas():
    etiquetas_param = request.args.get('etiquetas')  # ej: "perro,negro,callejero,Campana,Buenos Aires"
    

    if not etiquetas_param:
        return jsonify({"error": "Se requiere al menos una etiqueta"}), 400

    etiquetas = [normalizar_texto(tag) for tag in etiquetas_param.split(',') if tag.strip()]

    publicaciones = obtener_publicaciones_por_etiquetas(etiquetas)
    return jsonify(publicaciones), 200


# PATCH
@publicaciones_bp.route('/publicaciones/<int:id_publicacion>', methods=['PATCH'])
def actualizar(id_publicacion):
    data = request.get_json()
    try:
        actualizar_publicacion(id_publicacion, data)
        return jsonify({'mensaje': 'Publicación actualizada con éxito'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400



#DELETE
@publicaciones_bp.route('/publicaciones/<int:id_publicacion>', methods=['DELETE'])
def borrar_publicacion(id_publicacion):
    try:
        eliminar_publicacion(id_publicacion)
        return jsonify({'mensaje': 'Publicación eliminada correctamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400




