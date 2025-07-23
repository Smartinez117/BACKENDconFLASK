from app import app
from core.models import db, Etiqueta

with app.app_context():
    etiquetas = [
        Etiqueta(nombre='Perro'),
        Etiqueta(nombre='Gato')
    ]
    db.session.add_all(etiquetas)
    db.session.commit()
    print("Etiquetas agregadas con éxito")
