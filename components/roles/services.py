from core.models import db, Rol
from sqlalchemy.exc import SQLAlchemyError

def obtener_roles():
    """Devuelve todos los roles disponibles"""
    try:
        roles = Rol.query.all()
        return [{"id": r.id, "nombre": r.nombre} for r in roles]
    except SQLAlchemyError as e:
        print(f"Error al obtener roles: {e}")
        return []

def crear_rol(nombre):
    """Crea un nuevo rol"""
    try:
        nuevo_rol = Rol(nombre=nombre)
        db.session.add(nuevo_rol)
        db.session.commit()
        return {"id": nuevo_rol.id, "nombre": nuevo_rol.nombre}
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error al crear rol: {e}")
        return None

def actualizar_rol(id, nombre):
    """Actualiza un rol existente"""
    try:
        rol = Rol.query.get(id)
        if not rol:
            return None
        rol.nombre = nombre
        db.session.commit()
        return {"id": rol.id, "nombre": rol.nombre}
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error al actualizar rol: {e}")
        return None

def eliminar_rol(id):
    """Elimina un rol existente"""
    try:
        rol = Rol.query.get(id)
        if not rol:
            return None
        db.session.delete(rol)
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error al eliminar rol: {e}")
        return False
