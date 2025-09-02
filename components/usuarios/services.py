from flask import jsonify
from core.models import Usuario,db
from datetime import datetime,timezone
import pytz

zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")

def actualizar_datos_usuario(id_usuario,data):
    
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        raise Exception("Usuario no encontrado")

    usuario.nombre = data.get('nombre', usuario.nombre)
    usuario.telefono_pais = data.get('telefono_pais', usuario.telefono_pais)
    usuario.telefono_numero_local = data.get('telefono_numero_local', usuario.telefono_numero_local)
    usuario.descripcion = data.get('descripcion', usuario.descripcion)
    usuario.rol = data.get('rol',usuario.rol)
    usuario.fecha_modificacion = datetime.now(timezone.utc)

    db.session.commit()
       
def get_usuario (id_usuario):
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    return {
        'id':usuario.id,
        'firebase_uid':usuario.id,
        'nombre':usuario.nombre,
        'email': usuario.email,
        'foto_perfil_url':usuario.foto_perfil_url,
        'rol': usuario.rol,
        'fecha_registro': usuario.fecha_registro.astimezone(zona_arg).isoformat() if usuario.fecha_registro else None,
        'telefono_pais':usuario.telefono_pais,
        'telefono_numero_local':usuario.telefono_numero_local,
        'descripcion': usuario.descripcion

    }

def filtrar_usuarios_service(filtros):
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
        query = query.filter(Usuario.rol == filtros["rol"])

    usuarios = query.all()

    return [
        {
            "id": u.id,
            "nombre": u.nombre,
            "email": u.email,
            "foto_perfil_url": u.foto_perfil_url,
            "rol": u.rol,
            "telefono_pais": u.telefono_pais,
            "telefono_numero_local": u.telefono_numero_local,
            "descripcion": u.descripcion,
            "fecha_registro": u.fecha_registro.astimezone(zona_arg).isoformat() if u.fecha_registro else None
        }
        for u in usuarios
    ]

#funcion para obtener los datos del usuario por uid
def obtener_usuario_por_uid(uid):
    usuario = Usuario.query.filter_by(firebase_uid=uid).first()

    if not usuario:
        return None

    return {
        'id': usuario.id,
        'firebase_uid': usuario.firebase_uid,
        'nombre': usuario.nombre,
        'email': usuario.email,
        'foto_perfil_url': usuario.foto_perfil_url,
        'rol': usuario.rol,
        'fecha_registro': usuario.fecha_registro.astimezone(zona_arg).isoformat() if usuario.fecha_registro else None,
        'telefono_pais': usuario.telefono_pais,
        'telefono_numero_local': usuario.telefono_numero_local,
        'descripcion': usuario.descripcion
    }

