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
    
@ubicacion_bp.route('/localidades/<int:id>', methods=['GET'])
def obtener_localidad(id):
    localidad = Localidad.query.get(id)

    if not localidad:
        return jsonify({'error': 'Localidad no encontrada'}), 404

    return jsonify({
        'id': localidad.id,
        'nombre': localidad.nombre,
        'id_departamento': localidad.id_departamento,
        'latitud': float(localidad.latitud) if localidad.latitud else None,
        'longitud': float(localidad.longitud) if localidad.longitud else None
    })   

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


# --- PUT Localidad (actualizar) ---
@ubicacion_bp.route('/localidades/<int:id_localidad>', methods=['PATCH'])
def actualizar_localidad(id_localidad):
    data = request.get_json()
    localidad = Localidad.query.get(id_localidad)

    if not localidad:
        return jsonify({"error": "Localidad no encontrada"}), 404

    localidad.nombre = data.get('nombre', localidad.nombre)
    localidad.latitud = data.get('latitud', localidad.latitud)
    localidad.longitud = data.get('longitud', localidad.longitud)
    localidad.id_departamento = data.get('id_departamento', localidad.id_departamento)

    db.session.commit()

    return jsonify({
        "id": localidad.id,
        "nombre": localidad.nombre,
        "latitud": localidad.latitud,
        "longitud": localidad.longitud
    })

# --- DELETE Localidad ---
@ubicacion_bp.route('/localidades/<int:id_localidad>', methods=['DELETE'])
def eliminar_localidad(id_localidad):
    localidad = Localidad.query.get(id_localidad)

    if not localidad:
        return jsonify({"error": "Localidad no encontrada"}), 404

    db.session.delete(localidad)
    db.session.commit()

    return jsonify({"mensaje": "Localidad eliminada correctamente"})