from flask import jsonify
from core.models import Usuario,db
from datetime import datetime,timezone
import pytz

zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")

def actualizar_datos_usuario(id_usuario,data):
    '''Actualiza la información de un usuario existente.'''
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        raise Exception("Usuario no encontrado")

    usuario.nombre = data.get('nombre', usuario.nombre)
    usuario.telefono_pais = data.get('telefono_pais', usuario.telefono_pais)
    usuario.telefono_numero_local = data.get('telefono_numero_local', usuario.telefono_numero_local)
    usuario.descripcion = data.get('descripcion', usuario.descripcion)
    usuario.role_id = data.get("role_id", usuario.role_id)
    usuario.fecha_modificacion = datetime.now(timezone.utc)

    db.session.commit()

def get_usuario (id_usuario):
    ''' Obtiene la información de un usuario por su ID.'''
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    return {
        'id':usuario.id,
        'firebase_uid':usuario.firebase_uid,
        'nombre':usuario.nombre,
        'email': usuario.email,
        'foto_perfil_url':usuario.foto_perfil_url,
        'rol': usuario.rol_obj.nombre if usuario.rol_obj else None,
        'fecha_registro': (
            usuario.fecha_registro.astimezone(zona_arg).isoformat()
            if usuario.fecha_registro else None
        ),
        'telefono_pais':usuario.telefono_pais,
        'telefono_numero_local':usuario.telefono_numero_local,
        'descripcion': usuario.descripcion,
        'slug': usuario.slug,
        'estado': usuario.estado

    }

def obtener_usuario_por_slug(slug):
    '''funcion para obtener los datos del usuario por slug'''
    usuario = Usuario.query.filter_by(slug=slug).first()

    if not usuario:
        return None

    return {
        'id': usuario.id,
        'firebase_uid': usuario.firebase_uid,
        'nombre': usuario.nombre,
        'email': usuario.email,
        'foto_perfil_url': usuario.foto_perfil_url,
        "rol": usuario.rol_obj.nombre if usuario.rol_obj else None,
        'fecha_registro': (
            usuario.fecha_registro.astimezone(zona_arg).isoformat()
            if usuario.fecha_registro else None
        ),
        'telefono_pais': usuario.telefono_pais,
        'telefono_numero_local': usuario.telefono_numero_local,
        'descripcion': usuario.descripcion,
        'slug': usuario.slug,
        'estado': usuario.estado

    }


def filtrar_usuarios_service(filtros):
    '''Función para filtrar usuarios por email, nombre, teléfono y rol.'''
    query = Usuario.query

    if filtros.get("email"):
        query = query.filter(Usuario.email.ilike(f"%{filtros['email']}%"))
    if filtros.get("nombre"):
        query = query.filter(Usuario.nombre.ilike(f"%{filtros['nombre']}%"))
    if filtros.get("telefono_pais"):
        query = query.filter(Usuario.telefono_pais == filtros["telefono_pais"])
    if filtros.get("telefono_numero_local"):
        try:
            telefono = int(filtros["telefono_numero_local"])
            query = query.filter(Usuario.telefono_numero_local == telefono)
        except ValueError:
            raise ValueError("Número de teléfono inválido")
    if filtros.get("rol"):
        query = query.join(Usuario.rol_obj).filter(Rol.nombre == filtros["rol"])

    usuarios = query.all()

    return [
        {
            "id": u.id,
            "nombre": u.nombre,
            "email": u.email,
            "foto_perfil_url": u.foto_perfil_url,
            "rol": u.rol_obj.nombre if u.rol_obj else None,
            "telefono_pais": u.telefono_pais,
            "telefono_numero_local": u.telefono_numero_local,
            "descripcion": u.descripcion,
            'fecha_registro': (
                u.fecha_registro.astimezone(zona_arg).isoformat()
                if u.fecha_registro else None
            ),
        }
        for u in usuarios
    ]

#funcion para obtener los datos del usuario por uid
def obtener_usuario_por_uid(uid):
    '''Función para obtener los datos del usuario por uid.'''
    usuario = Usuario.query.filter_by(firebase_uid=uid).first()

    if not usuario:
        return None

    return {
        'id': usuario.id,
        'firebase_uid': usuario.firebase_uid,
        'nombre': usuario.nombre,
        'email': usuario.email,
        'foto_perfil_url': usuario.foto_perfil_url,
        "rol": usuario.rol_obj.nombre if usuario.rol_obj else None,
        'fecha_registro': (
            usuario.fecha_registro.astimezone(zona_arg).isoformat()
            if usuario.fecha_registro else None
        ),
        'telefono_pais': usuario.telefono_pais,
        'telefono_numero_local': usuario.telefono_numero_local,
        'descripcion': usuario.descripcion,
        'slug': usuario.slug,
        'estado': usuario.estado
    }
