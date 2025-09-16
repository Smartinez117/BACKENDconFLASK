import datetime
import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric
from slugify import slugify

db = SQLAlchemy()

class Usuario(db.Model):
    """Modelo de usuario para la base de datos."""
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(28), nullable=False)
    nombre = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    foto_perfil_url = db.Column(db.Text)
    rol = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime(timezone=True))
    telefono_pais = db.Column(db.Text)
    telefono_numero_local = db.Column(db.BigInteger)
    descripcion = db.Column(db.Text)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    publicaciones = db.relationship('Publicacion', backref='usuario', lazy=True)

    def generar_slug(self):
        """Genera un slug único basado en el nombre del usuario."""
        base_slug = slugify(self.nombre)
        unique_suffix = uuid.uuid4().hex[:6]  # ej: "772123"
        self.slug = f"{base_slug}{unique_suffix}"

    def to_dict(self):
        """Convierte la publicación a un diccionario serializable."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "foto_perfil_url": self.foto_perfil_url,
            "slug": self.slug
        }


class Etiqueta(db.Model):
    """Modelo de etiqueta para publicaciones."""
    __tablename__ = 'etiquetas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    publicaciones = db.relationship('Publicacion', secondary='publicacion_etiqueta', back_populates='etiquetas')


class PublicacionEtiqueta(db.Model):
    """Tabla de relación entre publicaciones y etiquetas."""
    __tablename__ = 'publicacion_etiqueta'
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id'), primary_key=True)
    id_etiqueta = db.Column(db.Integer, db.ForeignKey('etiquetas.id'), primary_key=True)


class Publicacion(db.Model):
    """Modelo de publicación."""
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
    imagenes = db.relationship('Imagen', backref='publicacion', lazy='select')
    localidad = db.relationship("Localidad", backref="publicaciones")
    reportes = db.relationship('Reporte',backref='publicacion',cascade="all, delete-orphan",passive_deletes=True)

    def to_dict(self):
        """Convierte la publicación a un diccionario serializable."""
        return {
            "id": self.id,
            "id_usuario": self.id_usuario,
            "id_locacion": self.id_locacion,
            "titulo": self.titulo,
            "categoria": self.categoria,
            "descripcion": self.descripcion,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_modificacion": self.fecha_modificacion.isoformat() if self.fecha_modificacion else None,
            "coordenadas": self.coordenadas,
            "etiquetas": [etiqueta.nombre for etiqueta in self.etiquetas],  # asumiendo que `Etiqueta` tiene `nombre`
            "imagenes": [img.url for img in self.imagenes],  # asumiendo que `Imagen` tiene `url`
            "localidad": self.localidad.nombre if self.localidad else None
        }

class Comentario(db.Model):
    """Modelo de comentario en publicaciones."""
    __tablename__ = 'comentarios'
    id = db.Column(db.Integer, primary_key=True)
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_anterior = db.Column(db.Integer)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime(timezone=True), nullable=False)
    fecha_modificacion = db.Column(db.DateTime(timezone=True))

class Imagen(db.Model):
    """Modelo de imagen asociada a publicaciones."""
    __tablename__ = 'imagenes'
    id = db.Column(db.Integer, primary_key=True)
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id'))
    url = db.Column(db.Text)

class Provincia(db.Model):
    """Modelo de provincia."""
    __tablename__ = 'provincias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text)
    latitud = db.Column(Numeric(15, 10))
    longitud = db.Column(Numeric(15, 10))

class Departamento(db.Model):
    """Modelo de departamento."""
    __tablename__ = 'departamentos'
    id = db.Column(db.Integer, primary_key=True)
    id_provincia = db.Column(db.Integer, db.ForeignKey('provincias.id'))
    nombre = db.Column(db.Text)
    latitud = db.Column(Numeric(15, 10))
    longitud = db.Column(Numeric(15, 10))

class Localidad(db.Model):
    """Modelo de localidad."""
    __tablename__ = 'localidades'
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.Text)
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamentos.id'))
    latitud = db.Column(Numeric(15, 10))
    longitud = db.Column(Numeric(15, 10))

class Notificacion(db.Model):
    """Modelo de notificación para usuarios."""
    __tablename__ = 'notificaciones'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id'), nullable=True)
    titulo = db.Column(db.Text)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime(timezone=True), nullable=False)
    leido = db.Column(db.Boolean, default=False)

class Reporte(db.Model):
    """Modelo de reporte de publicaciones."""
    __tablename__ = 'reportes'
    id = db.Column(db.Integer, primary_key=True)
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id',ondelete = 'CASCADE'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete="CASCADE"), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime(timezone=True), nullable=False)
    