from core.models import Imagen, db
from flask import jsonify

def obtener_todas_las_imagenes():
    imagenes = Imagen.query.all()
    resultado = []

    for img in imagenes:
        resultado.append({
            'id': img.id,
            'id_publicacion': img.id_publicacion,
            'url': img.url
        })

    return resultado

def obtener_imagenes_por_publicacion(id_publicacion):
    imagenes = Imagen.query.filter_by(id_publicacion=id_publicacion).all()
    resultado = []

    for img in imagenes:
        resultado.append({
            'id': img.id,
            'id_publicacion': img.id_publicacion,
            'url': img.url
        })

    return resultado


def crear_imagen(data):
    try:
        nueva_imagen = Imagen(
            id_publicacion=data.get("id_publicacion"),
            url=data.get("url")
        )
        db.session.add(nueva_imagen)
        db.session.commit()
        return jsonify({"mensaje": "Imagen creada exitosamente", "id": nueva_imagen.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


def eliminar_imagen(id_imagen):
    imagen = Imagen.query.get(id_imagen)

    if not imagen:
        return jsonify({"error": "Imagen no encontrada"}), 404

    try:
        db.session.delete(imagen)
        db.session.commit()
        return jsonify({"mensaje": "Imagen eliminada exitosamente"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400