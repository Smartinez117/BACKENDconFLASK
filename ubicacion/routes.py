from flask import Blueprint, jsonify, request
from core.models import db, Provincia, Departamento, Localidad

ubicacion_bp = Blueprint('ubicacion', __name__, url_prefix='/api/ubicacion')


@ubicacion_bp.route('/provincias', methods=['GET'])
def obtener_provincias():
    provincias = Provincia.query.order_by(Provincia.nombre).all()
    return jsonify([{'id': p.id, 'nombre': p.nombre} for p in provincias])


@ubicacion_bp.route('/departamentos', methods=['GET'])
def obtener_departamentos():
    provincia_id = request.args.get('provincia_id')
    if not provincia_id:
        return jsonify({"error": "Falta el parámetro provincia_id"}), 400
    
    departamentos = Departamento.query.filter_by(id_provincia=provincia_id).order_by(Departamento.nombre).all()

    return jsonify([{'id': d.id, 'nombre': d.nombre} for d in departamentos])


@ubicacion_bp.route('/localidades', methods=['GET'])
def obtener_localidades():
    departamento_id = request.args.get('departamento_id')
    if not departamento_id:
        return jsonify({"error": "Falta el parámetro departamento_id"}), 400
    
    localidades = Localidad.query.filter_by(id_departamento=departamento_id).order_by(Localidad.nombre).all()
    return jsonify([
        {
            'id': l.id,
            'nombre': l.nombre,
            'latitud': l.latitud,
            'longitud': l.longitud
        } for l in localidades
    ])