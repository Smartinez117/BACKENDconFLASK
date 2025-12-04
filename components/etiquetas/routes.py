from flask import Blueprint, request, jsonify
from core.models import db, Etiqueta
from sqlalchemy.exc import IntegrityError

etiquetas_bp = Blueprint('etiquetas', __name__)


@etiquetas_bp.route('/api/etiquetas', methods=['GET'])
def listar_etiquetas():
    """Lista todas las etiquetas ordenadas por nombre."""
    etiquetas = Etiqueta.query.order_by(Etiqueta.nombre).all()
    return jsonify([{"id": e.id, "nombre": e.nombre} for e in etiquetas])


@etiquetas_bp.route('/api/etiquetas', methods=['POST'])
def crear_etiqueta():
    """Crea una nueva etiqueta si el nombre es válido y no existe."""
    data = request.json
    nombre = data.get("nombre", "").strip()
    if not nombre:
        return jsonify({"error": "El nombre es obligatorio"}), 400
    if Etiqueta.query.filter_by(nombre=nombre).first():
        return jsonify({"error": "La etiqueta ya existe"}), 409

    etiqueta = Etiqueta(nombre=nombre)
    db.session.add(etiqueta)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Error al guardar"}), 500

    return jsonify({"id": etiqueta.id, "nombre": etiqueta.nombre}), 201


@etiquetas_bp.route('/api/etiquetas/<int:id_etiqueta>', methods=['GET'])
def obtener_etiqueta(id_etiqueta):
    """Obtiene una etiqueta por su ID."""
    etiqueta = Etiqueta.query.get(id_etiqueta)
    if not etiqueta:
        return jsonify({"error": "Etiqueta no encontrada"}), 404
    return jsonify({"id": etiqueta.id, "nombre": etiqueta.nombre})


@etiquetas_bp.route('/api/etiquetas/<int:id_etiqueta>', methods=['PATCH'])
def actualizar_etiqueta(id_etiqueta):
    """Actualiza el nombre de una etiqueta existente."""
    etiqueta = Etiqueta.query.get(id_etiqueta)
    if not etiqueta:
        return jsonify({"error": "Etiqueta no encontrada"}), 404

    data = request.json
    nuevo_nombre = data.get("nombre", "").strip()
    if not nuevo_nombre:
        return jsonify({"error": "El nombre es obligatorio"}), 400

    if Etiqueta.query.filter(Etiqueta.nombre == nuevo_nombre, Etiqueta.id != id_etiqueta).first():
        return jsonify({"error": "Otra etiqueta con ese nombre ya existe"}), 409

    etiqueta.nombre = nuevo_nombre
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar"}), 500

    return jsonify({"id": etiqueta.id, "nombre": etiqueta.nombre})


@etiquetas_bp.route('/api/etiquetas/<int:id_etiqueta>', methods=['DELETE'])
def eliminar_etiqueta(id_etiqueta):
    """Elimina una etiqueta por su ID."""
    etiqueta = Etiqueta.query.get(id_etiqueta)
    if not etiqueta:
        return jsonify({"error": "Etiqueta no encontrada"}), 404

    db.session.delete(etiqueta)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "No se pudo eliminar, puede estar en uso"}), 500

    return jsonify({"mensaje": "Etiqueta eliminada correctamente"})
