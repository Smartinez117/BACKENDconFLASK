from datetime import datetime, timezone
import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric, event
from sqlalchemy.orm import Session
from slugify import slugify

db = SQLAlchemy()

# --- FUNCIONES AUXILIARES ---

def _to_str_safe(v):
    """Convierte un valor a string de forma segura (maneja bytes, None, etc)."""
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


# --- MODELOS DE UBICACIÓN ---

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
    
    # Relación para acceder a la provincia desde el departamento
    provincia = db.relationship('Provincia', backref='departamentos')

class Localidad(db.Model):
    """Modelo de localidad."""
    __tablename__ = 'localidades'
    id = db.Column(db.BigInteger, primary_key=True)
    nombre = db.Column(db.Text)
    id_departamento = db.Column(db.Integer, db.ForeignKey('departamentos.id'))
    latitud = db.Column(Numeric(15, 10))
    longitud = db.Column(Numeric(15, 10))

    # Relación para acceder al departamento desde la localidad
    departamento = db.relationship('Departamento', backref='localidades')


# --- MODELOS PRINCIPALES ---

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
    
    # Relación opcional con la tabla 'localidades'
    id_localidad = db.Column(db.BigInteger, db.ForeignKey('localidades.id'), nullable=True)
    
    # Propiedad para acceder al objeto localidad directamente (usuario.localidad.nombre)
    localidad_obj = db.relationship('Localidad', backref='usuarios')

    # Cascada para publicaciones y comentarios
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

    # --- REPORTES ---
    
    # 1. Reportes que este usuario HA CREADO (es el denunciante)
    reportes_realizados = db.relationship(
        'Reporte',
        foreign_keys='Reporte.id_usuario', 
        backref='denunciante',             
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # 2. Reportes que este usuario HA RECIBIDO (es el denunciado)
    reportes_recibidos = db.relationship(
        'Reporte',
        foreign_keys='Reporte.id_usuario_reportado', 
        backref='denunciado',                        
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def generar_slug(self):
        """Genera un slug único basado en el nombre del usuario."""
        nombre = _to_str_safe(self.nombre)
        try:
            base_slug = slugify(nombre)
            if not isinstance(base_slug, str):
                base_slug = str(base_slug)
        except Exception:
            base_slug = 'u'
        candidate = f"{base_slug}{uuid.uuid4().hex[:6]}"
        # Nota: self.query puede no funcionar si no se hereda de db.Model con query property,
        # es mejor usar Usuario.query o db.session.query(Usuario)
        while Usuario.query.filter_by(slug=candidate).first():
            candidate = f"{base_slug}{uuid.uuid4().hex[:6]}"
        self.slug = candidate

    def to_dict(self):
        """Convierte el usuario a un diccionario serializable con toda la info."""
        
        # Construimos la info de ubicación completa si existe
        ubicacion_info = None
        if self.localidad_obj:
            loc = self.localidad_obj
            
            # Obtenemos IDs jerárquicos gracias a las nuevas relaciones agregadas
            id_provincia = None
            if loc.departamento:
                 id_provincia = loc.departamento.id_provincia

            ubicacion_info = {
                "id": loc.id,
                "nombre": loc.nombre,
                "id_departamento": loc.id_departamento,
                "id_provincia": id_provincia
            }
            
        return {
            "id": self.id,
            "firebase_uid": self.firebase_uid,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol_obj.nombre if self.rol_obj else None,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "foto_perfil_url": self.foto_perfil_url,
            "slug": self.slug,
            "estado": self.estado,
            "telefono_pais": self.telefono_pais,
            "telefono_numero_local": self.telefono_numero_local,
            "descripcion": self.descripcion,
            "id_localidad": self.id_localidad,
            "ubicacion": ubicacion_info
        }

# Evento para generar slug automáticamente antes de insertar
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
    sess = Session(bind=connection)
    while sess.query(Usuario).filter_by(slug=candidate).first():
        candidate = f"{base_slug}{uuid.uuid4().hex[:6]}"
    target.slug = candidate


class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)

    publicaciones = db.relationship("Publicacion", back_populates="categoria_obj")


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
    id_categoria = db.Column(
        db.Integer,
        db.ForeignKey('categorias.id', ondelete='SET NULL'),
        nullable=True
    )

    categoria_obj = db.relationship("Categoria", back_populates="publicaciones")
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
            "categoria": {
                "id": self.categoria_obj.id,
                "nombre": self.categoria_obj.nombre,
                "descripcion": self.categoria_obj.descripcion
            } if self.categoria_obj else None,
            "descripcion": self.descripcion,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "fecha_modificacion": self.fecha_modificacion.isoformat() if self.fecha_modificacion else None,
            "coordenadas": self.coordenadas,
            "estado": self.estado,
            "etiquetas": [etiqueta.nombre for etiqueta in self.etiquetas],
            "imagenes": [img.url for img in self.imagenes],
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
    
    # Sirve para guardar el ID de la SolicitudContacto, o de un Reporte, etc.
    id_referencia = db.Column(db.Integer, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "id_usuario": self.id_usuario,
            "id_publicacion": self.id_publicacion,
            "id_referencia": self.id_referencia, # <--- IMPORTANTE
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "tipo": self.tipo,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "leido": self.leido
        }

class Reporte(db.Model):
    __tablename__ = 'reportes'
    id = db.Column(db.Integer, primary_key=True)
    
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id', ondelete='CASCADE'), nullable=True)
    id_comentario = db.Column(db.Integer, db.ForeignKey('comentarios.id', ondelete='CASCADE'), nullable=True)
    id_usuario_reportado = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=True)

    # Usuario que HACE el reporte
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime(timezone=True), nullable=False)

    @property
    def objetivo(self):
        if self.id_publicacion:
            return "Publicación"
        elif self.id_comentario:
            return "Comentario"
        elif self.id_usuario_reportado:
            return "Usuario"
        return "Desconocido"

class Rol(db.Model):
    """Modelo de rol para usuarios."""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

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
        
        
        

class SolicitudContacto(db.Model):
    __tablename__ = 'solicitudes_contacto'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Quién quiere contactar (El que encontró el perro o quiere adoptar)
    id_solicitante = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    
    # El dueño de la publicación
    id_receptor = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    
    # Sobre qué publicación es
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id', ondelete='CASCADE'), nullable=False)
    
    mensaje = db.Column(db.Text) # "Hola, encontré a tu perro..."
    
    tipo_contacto = db.Column(db.String(20), nullable=False, default='whatsapp')
    
    # Estados: 0=Pendiente, 1=Aceptada, 2=Rechazada
    estado = db.Column(db.Integer, default=0) 
    
    fecha_creacion = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))

    # Relaciones
    solicitante = db.relationship('Usuario', foreign_keys=[id_solicitante], backref='solicitudes_enviadas')
    receptor = db.relationship('Usuario', foreign_keys=[id_receptor], backref='solicitudes_recibidas')
    
    publicacion = db.relationship('Publicacion', backref=db.backref('solicitudes', cascade='all, delete-orphan'))
    
    def to_dict(self):
        return {
            "id": self.id,
            "id_usuario": self.id_usuario,
            "id_publicacion": self.id_publicacion,
            "id_referencia": self.id_referencia, # <--- ESTO ES LO QUE FALTABA
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "tipo": self.tipo,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "leido": self.leido
        }