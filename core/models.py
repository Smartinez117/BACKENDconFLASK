import datetime
import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric
from slugify import slugify
from sqlalchemy import event
import uuid

db = SQLAlchemy()

class Usuario(db.Model):
    """Modelo de usuario para la base de datos."""
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(28), nullable=False)
    nombre = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    foto_perfil_url = db.Column(db.Text)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False, default=1)
    rol_obj = db.relationship('Rol', back_populates='usuarios')
    fecha_registro = db.Column(db.DateTime(timezone=True))
    telefono_pais = db.Column(db.Text)
    telefono_numero_local = db.Column(db.BigInteger)
    descripcion = db.Column(db.Text)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    estado = db.Column(db.String(10), nullable=False, default="activo")

    # Cascada para publicaciones, comentarios y reportes
    publicaciones = db.relationship(
        'Publicacion',
        backref='usuario',
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    comentarios = db.relationship(
        'Comentario',
        backref='usuario',
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    reportes = db.relationship(
        'Reporte',
        backref='usuario',
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True
    )


    def generar_slug(self):
        """Genera un slug único basado en el nombre del usuario (forzando str)."""
        nombre = _to_str_safe(self.nombre)
        try:
            base_slug = slugify(nombre)
            if not isinstance(base_slug, str):
                base_slug = str(base_slug)
        except Exception:
            base_slug = 'u'
        candidate = f"{base_slug}{uuid.uuid4().hex[:6]}"
        while Usuario.query.filter_by(slug=candidate).first():
            candidate = f"{base_slug}{uuid.uuid4().hex[:6]}"
        self.slug = candidate

    def to_dict(self):
        """Convierte la publicación a un diccionario serializable."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol_obj.nombre if self.rol_obj else None,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "foto_perfil_url": self.foto_perfil_url,
            "slug": self.slug,
            "estado": self.estado
        }
  

def _to_str_safe(v):
        if v is None:
            return ''
        if isinstance(v, str):
            return v
        if isinstance(v, (bytes, bytearray)):
            try:
                return v.decode('utf-8')
            except Exception:
                return v.decode('latin-1', errors='replace')
        if isinstance(v, memoryview):
            try:
                return v.tobytes().decode('utf-8')
            except Exception:
                return v.tobytes().decode('latin-1', errors='replace')
        return str(v)
    
    
@event.listens_for(Usuario, 'before_insert')
def generar_slug_before_insert(mapper, connection, target):
    """Listener que normaliza nombre y genera un slug único antes de insertar."""
    nombre = _to_str_safe(getattr(target, 'nombre', ''))
    try:
        base_slug = slugify(nombre)
        if not isinstance(base_slug, str):
            base_slug = str(base_slug)
    except Exception:
        base_slug = 'u'
    candidate = f"{base_slug}{uuid.uuid4().hex[:6]}"
    from sqlalchemy.orm import Session
    sess = Session(bind=connection)
    while sess.query(Usuario).filter_by(slug=candidate).first():
        candidate = f"{base_slug}{uuid.uuid4().hex[:6]}"
    target.slug = candidate

class Etiqueta(db.Model):
    """Modelo de etiqueta para publicaciones."""
    __tablename__ = 'etiquetas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    publicaciones = db.relationship('Publicacion', secondary='publicacion_etiqueta', back_populates='etiquetas')


class PublicacionEtiqueta(db.Model):
    """Tabla de relación entre publicaciones y etiquetas."""
    __tablename__ = 'publicacion_etiqueta'
    id_publicacion = db.Column(
        db.Integer, 
        db.ForeignKey('publicaciones.id', ondelete='CASCADE'), 
        primary_key=True
    )
    id_etiqueta = db.Column(
        db.Integer, 
        db.ForeignKey('etiquetas.id', ondelete='CASCADE'), 
        primary_key=True
    )


class Publicacion(db.Model):
    __tablename__ = 'publicaciones'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id', ondelete='CASCADE'),
        nullable=False
    )
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
    reportes = db.relationship('Reporte', backref='publicacion', cascade="all, delete-orphan", passive_deletes=True)
    
    estado = db.Column(db.Integer, default=0)
  


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
            "estado": self.estado,
            "etiquetas": [etiqueta.nombre for etiqueta in self.etiquetas],  # asumiendo que `Etiqueta` tiene `nombre`
            "imagenes": [img.url for img in self.imagenes],  # asumiendo que `Imagen` tiene `url`
            "localidad": self.localidad.nombre if self.localidad else None
        }

class Comentario(db.Model):
    __tablename__ = 'comentarios'
    id = db.Column(db.Integer, primary_key=True)
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id', ondelete='CASCADE'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    id_anterior = db.Column(db.Integer)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime(timezone=True), nullable=False)
    fecha_modificacion = db.Column(db.DateTime(timezone=True))


class Imagen(db.Model):
    """Modelo de imagen asociada a publicaciones."""
    __tablename__ = 'imagenes'
    id = db.Column(db.Integer, primary_key=True)
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id', ondelete='CASCADE'))
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
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id', ondelete='CASCADE'), nullable=True)
    titulo = db.Column(db.Text)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime(timezone=True), nullable=False)
    leido = db.Column(db.Boolean, default=False)

class Reporte(db.Model):
    __tablename__ = 'reportes'
    id = db.Column(db.Integer, primary_key=True)
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id', ondelete='CASCADE'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime(timezone=True), nullable=False)

    

class Rol(db.Model):
    """Modelo de rol para usuarios."""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)  # ej: "user", "admin"

    # Relación con usuarios (un rol puede tener muchos usuarios)
    usuarios = db.relationship('Usuario', back_populates='rol_obj')
    
    
    
class RequestLog(db.Model):
    """Modelo para registrar logs de requests."""
    __tablename__ = "request_logs"

    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = db.Column(db.String, nullable=False)

    path = db.Column(db.Text)
    method = db.Column(db.String(10))

    timestamp_arrival = db.Column(db.DateTime(timezone=True))
    timestamp_start_processing = db.Column(db.DateTime(timezone=True))
    timestamp_send_supabase = db.Column(db.DateTime(timezone=True))
    timestamp_return_supabase = db.Column(db.DateTime(timezone=True))
    timestamp_send_cloudinary = db.Column(db.DateTime(timezone=True))
    timestamp_return_cloudinary = db.Column(db.DateTime(timezone=True))
    timestamp_send_firebase = db.Column(db.DateTime(timezone=True))
    timestamp_return_firebase = db.Column(db.DateTime(timezone=True))
    timestamp_response_sent = db.Column(db.DateTime(timezone=True))
    response_time_ms = db.Column(db.Integer, nullable=True)

    worker_id = db.Column(db.String)
    request_type = db.Column(db.String(50))

    payload_size = db.Column(db.Integer)
    image_size = db.Column(db.Integer)

    status_code = db.Column(db.Integer)
    error = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "request_id": self.request_id,
            "path": self.path,
            "method": self.method,
            "timestamp_arrival": self.timestamp_arrival.isoformat() if self.timestamp_arrival else None,
            "timestamp_start_processing": self.timestamp_start_processing.isoformat() if self.timestamp_start_processing else None,
            "timestamp_send_supabase": self.timestamp_send_supabase.isoformat() if self.timestamp_send_supabase else None,
            "timestamp_return_supabase": self.timestamp_return_supabase.isoformat() if self.timestamp_return_supabase else None,
            "timestamp_send_cloudinary": self.timestamp_send_cloudinary.isoformat() if self.timestamp_send_cloudinary else None,
            "timestamp_return_cloudinary": self.timestamp_return_cloudinary.isoformat() if self.timestamp_return_cloudinary else None,
            "timestamp_send_firebase": self.timestamp_send_firebase.isoformat() if self.timestamp_send_firebase else None,
            "timestamp_return_firebase": self.timestamp_return_firebase.isoformat() if self.timestamp_return_firebase else None,
            "timestamp_response_sent": self.timestamp_response_sent.isoformat() if self.timestamp_response_sent else None,
            "worker_id": self.worker_id,
            "request_type": self.request_type,
            "payload_size": self.payload_size,
            "image_size": self.image_size,
            "status_code": self.status_code,
            "error": self.error,
        }
