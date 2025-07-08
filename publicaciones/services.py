from flask import jsonify
from core.models import db, Publicacion
from datetime import datetime

def crear_publicacion(data):
    nueva = Publicacion(
        titulo=data["titulo"],
        descripcion=data["descripcion"],
        categoria=data["categoria"],
        fecha_creacion=datetime.utcnow(),
        # otros campos...
    )
    db.session.add(nueva)
    db.session.commit()
    return {"message": "Publicación creada"}, 201

def obtener_publicaciones(categoria=None):
    query = Publicacion.query
    if categoria:
        query = query.filter_by(categoria=categoria)
    return jsonify([pub.to_dict() for pub in query.all()])
