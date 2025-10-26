#servicios que solo necesitara el adminitrador
#algunos serán similares o reducidos de su versión original por el hecho que el admin no puede editar todo para conservar la autenticidad y correcto funcionamiento de la sesion de usuario

from core.models import Usuario, db

def actualizar_datos_usuario(id_usuario, data):
    """
    Actualiza solo nombre y rol de un usuario.
    """
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        return None

    usuario.nombre = data.get("nombre", usuario.nombre)
    usuario.role_id = data.get("role_id", usuario.role_id)

    db.session.commit()

    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "fecha_registro": usuario.fecha_registro,
        "rol": usuario.rol_obj.nombre if usuario.rol_obj else None,
        "role_id": usuario.role_id
    }
