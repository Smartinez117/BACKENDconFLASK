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
    
    

@ubicacion_bp.route('/localidades', methods=['POST'])
def crear_localidad():
    data = request.get_json()
    nombre = data.get('nombre')
    latitud = data.get('latitud')
    longitud = data.get('longitud')
    id_departamento = data.get('id_departamento')

    if not all([nombre, latitud, longitud, id_departamento]):
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    nueva_localidad = Localidad(
        nombre=nombre,
        latitud=latitud,
        longitud=longitud,
        id_departamento=id_departamento
    )
    db.session.add(nueva_localidad)
    db.session.commit()

    return jsonify({
        "id": nueva_localidad.id,
        "nombre": nueva_localidad.nombre,
        "latitud": nueva_localidad.latitud,
        "longitud": nueva_localidad.longitud
    }), 201
