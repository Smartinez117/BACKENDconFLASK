import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric

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


class Etiqueta(db.Model):
    __tablename__ = 'etiquetas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    publicaciones = db.relationship('Publicacion', secondary='publicacion_etiqueta', back_populates='etiquetas')


class PublicacionEtiqueta(db.Model):
    __tablename__ = 'publicacion_etiqueta'
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id'), primary_key=True)
    id_etiqueta = db.Column(db.Integer, db.ForeignKey('etiquetas.id'), primary_key=True)


class Publicacion(db.Model):
    __tablename__ = 'publicaciones'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_locacion = db.Column(db.BigInteger, db.ForeignKey('localidades.id'))
    titulo = db.Column(db.Text)
    categoria = db.Column(db.Text, nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime(timezone=True))
    fecha_modificacion = db.Column(db.DateTime(timezone=True))
    coordenadas = db.Column(db.ARRAY(db.Float))

    etiquetas = db.relationship('Etiqueta', secondary='publicacion_etiqueta', back_populates='publicaciones')

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
    __tablename__ = 'provincias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text)
    latitud = db.Column(Numeric(15, 10))
    longitud = db.Column(Numeric(15, 10))

class Departamento(db.Model):
    __tablename__ = 'departamentos'
    id = db.Column(db.Integer, primary_key=True)
    id_provincia = db.Column(db.Integer, db.ForeignKey('provincias.id'))
    nombre = db.Column(db.Text)
    latitud = db.Column(Numeric(15, 10))
    longitud = db.Column(Numeric(15, 10))

class Localidad(db.Model):
    __tablename__ = 'localidades'
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.Text)
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamentos.id'))
    latitud = db.Column(Numeric(15, 10))
    longitud = db.Column(Numeric(15, 10))

    
    
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