from flask import jsonify
from core.models import Usuario,db
from datetime import datetime

def actualizar_datos_usuario(id_usuario,data):
    
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    usuario.nombre = data.get('nombre', usuario.nombre)
    usuario.telefono_pais = data.get('telefono_pais', usuario.telefono_pais)
    usuario.telefono_numero_local = data.get('telefono_numero_local', usuario.telefono_numero_local)
    usuario.descripcion = data.get('descripcion', usuario.descripcion)
    usuario.fecha_modificacion = datetime.utcnow()

    db.session.commit()
       
def get_usuario (id_usuario):
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    return usuario