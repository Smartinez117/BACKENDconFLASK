#endpoints que solo necesitara el adminitrador
# components/funcionesAdmin/routes.py
from flask import Blueprint, request, jsonify
from core.models import db, Usuario, Publicacion
from components.funcionesAdmin.services import actualizar_datos_usuario
from firebase_admin import auth
from datetime import datetime



# Blueprint exclusivo para funciones de admin
admin_bp = Blueprint('admin', __name__)

# Endpoint para que el admin actualice nombre y rol de un usuario
@admin_bp.route('/admin/usuario/<int:id_usuario>', methods=['PATCH'])
def admin_actualizar_usuario(id_usuario):
    """
    Permite al administrador actualizar únicamente el nombre y rol de un usuario.
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se enviaron datos'}), 400

    try:
        usuario_actualizado = actualizar_datos_usuario(id_usuario, data)
        if not usuario_actualizado:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        return jsonify(usuario_actualizado), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Suspender usuario

@admin_bp.route('/admin/usuarios/<int:id_usuario>/suspender', methods=['PATCH'])
def suspender_usuario(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)
    try:
        auth.update_user(usuario.firebase_uid, disabled=True)
        usuario.estado = "suspendido"
        db.session.commit()
        return jsonify({
            "mensaje": f"Usuario {usuario.nombre} suspendido correctamente",
            "usuario": {"id": usuario.id, "estado": usuario.estado}
        }), 200
    except Exception as error:
        return jsonify({"error": f"No se pudo suspender al usuario: {str(error)}"}), 500

# Activar usuario
@admin_bp.route('/admin/usuarios/<int:id_usuario>/activar', methods=['PATCH'])
def activar_usuario(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)
    try:
        auth.update_user(usuario.firebase_uid, disabled=False)
        usuario.estado = "activo"
        db.session.commit()
        return jsonify({
            "mensaje": f"Usuario {usuario.nombre} activado correctamente",
            "usuario": {"id": usuario.id, "estado": usuario.estado}
        }), 200
    except Exception as error:
        return jsonify({"error": f"No se pudo activar al usuario: {str(error)}"}), 500
    
# Borrar usuario
@admin_bp.route('/admin/usuarios/<int:id_usuario>', methods=['DELETE'])
def eliminar_usuario(id_usuario):
    usuario = Usuario.query.get_or_404(id_usuario)
    try:
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({
            "mensaje": f"Usuario {usuario.nombre} borrado correctamente",
            "usuario": {"id": usuario.id}
        }), 200
    except Exception as error:
        return jsonify({"error": f"No se pudo borrar el usuario: {str(error)}"}), 500


@admin_bp.route('/admin/publicaciones', methods=['GET'])
def admin_obtener_publicaciones():
    """
    Devuelve publicaciones con datos del usuario + permite filtrado para administradores.
    """
    try:
        # Obtener parámetros de filtro
        id_usuario = request.args.get("id_usuario", type=int)
        categoria = request.args.get("categoria", type=str)
        estado = request.args.get("estado", type=str)
        provincia = request.args.get("provincia", type=str)
        departamento = request.args.get("departamento", type=str)
        localidad = request.args.get("localidad", type=str)
        fecha_desde = request.args.get("fecha_desde", type=str)
        fecha_hasta = request.args.get("fecha_hasta", type=str)

        # Base query
        query = Publicacion.query

        # Filtros dinámicos
        if id_usuario:
            query = query.filter(Publicacion.id_usuario == id_usuario)

        if categoria:
            query = query.filter(Publicacion.categoria == categoria)

        if estado:
            query = query.filter(Publicacion.estado == estado)

        if provincia:
            query = query.filter(Publicacion.provincia == provincia)

        if departamento:
            query = query.filter(Publicacion.departamento == departamento)

        if localidad:
            query = query.filter(Publicacion.localidad == localidad)

        if fecha_desde:
            try:
                fecha_ini = datetime.strptime(fecha_desde, "%Y-%m-%d")
                query = query.filter(Publicacion.fecha >= fecha_ini)
            except:
                pass

        if fecha_hasta:
            try:
                fecha_fin = datetime.strptime(fecha_hasta, "%Y-%m-%d")
                query = query.filter(Publicacion.fecha <= fecha_fin)
            except:
                pass

        publicaciones = query.all()

        # Armar JSON
        resultado = []
        for pub in publicaciones:
            usuario = pub.usuario  # relationship ya disponible

            resultado.append({
                **pub.to_dict(),
                "usuario": {
                    "id": usuario.id if usuario else None,
                    "nombre": usuario.nombre if usuario else None,
                    "email": usuario.email if usuario else None,
                }
            })

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
