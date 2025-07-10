import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(28), nullable=False)
    nombre = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    foto_perfil_url = db.Column(db.Text)
    rol = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime)
    telefono_pais = db.Column(db.Text)
    telefono_numero_local = db.Column(db.BigInteger)
    descripcion = db.Column(db.Text)
    publicaciones = db.relationship('Publicacion', backref='usuario', lazy=True)

class Publicacion(db.Model):
    __tablename__ = 'publicaciones'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_locacion = db.Column(db.Integer, db.ForeignKey('localidad.id'))
    titulo = db.Column(db.Text)
    categoria = db.Column(db.Text, nullable=False)
    etiquetas = db.Column(db.Text)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime)
    fecha_modificacion = db.Column(db.DateTime)
    coordenadas = db.Column(db.ARRAY(db.Float))

class Comentario(db.Model):
    __tablename__ = 'comentarios'
    id = db.Column(db.Integer, primary_key=True)
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_anterior = db.Column(db.Integer)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, nullable=False)
    fecha_modificacion = db.Column(db.DateTime)

class Imagen(db.Model):
    __tablename__ = 'imagenes'
    id = db.Column(db.Integer, primary_key=True)
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id'))
    url = db.Column(db.Text)

class Provincia(db.Model):
    __tablename__ = 'provincia'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text)

class PartidoDepartamento(db.Model):
    __tablename__ = 'partido_departamento'
    id = db.Column(db.Integer, primary_key=True)
    id_provincia = db.Column(db.Integer, db.ForeignKey('provincia.id'))
    nombre = db.Column(db.Text)

class Localidad(db.Model):
    __tablename__ = 'localidad'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text)
    id_departamento = db.Column(db.Text)
    
    
class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    titulo = db.Column(db.Text)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, nullable=False)
    leido = db.Column(db.Boolean, default=False)
    
    
class Reporte(db.Model):
    __tablename__ = 'reportes'
    id = db.Column(db.Integer, primary_key=True)
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, nullable=False)