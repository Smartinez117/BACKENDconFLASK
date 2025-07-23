from flask import Blueprint, request, jsonify
from core.models import db, Etiqueta, Publicacion
from sqlalchemy.exc import IntegrityError

etiquetas_bp = Blueprint('etiquetas', __name__)

@etiquetas_bp.route('/', methods=['GET'])
def listar_etiquetas():
    etiquetas = Etiqueta.query.order_by(Etiqueta.nombre).all()
    return jsonify([{"id": e.id, "nombre": e.nombre} for e in etiquetas])

@etiquetas_bp.route('/', methods=['POST'])
def crear_etiqueta():
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
