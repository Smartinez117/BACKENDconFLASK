#servicios que solo necesitara el adminitrador
#algunos serán similares o reducidos de su versión original por el hecho que el admin no puede editar todo para conservar la autenticidad y correcto funcionamiento de la sesion de usuario

from core.models import Usuario, db
from firebase_admin import auth as firebase_auth

def actualizar_datos_usuario(id_usuario, data):
    """
    Actualiza nombre y rol de un usuario, y sincroniza los custom claims
    admin de Firebase según el nuevo rol.
    """
    usuario = Usuario.query.get(id_usuario)
    if not usuario:
        return None

    # Guardar valores anteriores para detectar cambios si querés
    rol_viejo = usuario.role_id

    # --- Actualizar campos ---
    usuario.nombre = data.get("nombre", usuario.nombre)
    usuario.role_id = data.get("role_id", usuario.role_id)

    db.session.commit()

    # --- Actualizar claims en Firebase solo si tiene firebase_uid ---
    if usuario.firebase_uid:

        # Si ahora es admin (role_id == 2)
        if usuario.role_id == 2:
            firebase_auth.set_custom_user_claims(usuario.firebase_uid, {"admin": True})

        # Si ya no es admin
        else:
            firebase_auth.set_custom_user_claims(usuario.firebase_uid, None)

    # --- Respuesta al endpoint ---
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "fecha_registro": usuario.fecha_registro,
        "rol": usuario.rol_obj.nombre if usuario.rol_obj else None,
        "role_id": usuario.role_id
    }
