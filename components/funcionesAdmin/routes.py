# components/funcionesAdmin/routes.py
from flask import Blueprint, request, jsonify
from core.models import db, Usuario, Publicacion, Reporte
from components.funcionesAdmin.services import actualizar_datos_usuario
from firebase_admin import auth
from datetime import datetime
from core.auth_middleware import require_admin   # <--- IMPORTANTE


admin_bp = Blueprint('admin', __name__)


# --- Actualizar usuario ---
@admin_bp.route('/admin/usuario/<int:id_usuario>', methods=['PATCH'])
@require_admin
def admin_actualizar_usuario(id_usuario):
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


# --- Suspender usuario ---
@admin_bp.route('/admin/usuarios/<int:id_usuario>/suspender', methods=['PATCH'])
@require_admin
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
        return jsonify({"error": str(error)}), 500


# --- Activar usuario ---
@admin_bp.route('/admin/usuarios/<int:id_usuario>/activar', methods=['PATCH'])
@require_admin
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
        return jsonify({"error": str(error)}), 500


# --- Borrar usuario ---
@admin_bp.route('/admin/usuarios/<int:id_usuario>', methods=['DELETE'])
@require_admin
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
        return jsonify({"error": str(error)}), 500


# --- Publicaciones ---
@admin_bp.route('/admin/publicaciones', methods=['GET'])
#@require_admin
def admin_obtener_publicaciones():
    try:
        id_usuario = request.args.get("id_usuario", type=int)
        categoria = request.args.get("categoria", type=str)
        estado = request.args.get("estado", type=str)
        provincia = request.args.get("provincia", type=str)
        departamento = request.args.get("departamento", type=str)
        localidad = request.args.get("localidad", type=str)
        fecha_desde = request.args.get("fecha_desde", type=str)
        fecha_hasta = request.args.get("fecha_hasta", type=str)

        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=15, type=int)

        query = Publicacion.query

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

        query = query.order_by(Publicacion.fecha_creacion.desc())
        total = query.count()

        publicaciones = query.offset((page - 1) * limit).limit(limit).all()

        resultado = []
        for pub in publicaciones:
            usuario = pub.usuario
            resultado.append({
                **pub.to_dict(),
                "usuario": {
                    "id": usuario.id if usuario else None,
                    "nombre": usuario.nombre if usuario else None,
                    "email": usuario.email if usuario else None,
                }
            })

        return jsonify({
            "page": page,
            "limit": limit,
            "total": total,
            "publicaciones": resultado
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Estadísticas ---
@admin_bp.route('/admin/estadisticas', methods=['GET'])
#@require_admin
def admin_stats():
    try:
        total_usuarios = Usuario.query.count()
        total_publicaciones = Publicacion.query.count()
        total_reportes = Reporte.query.count()

        return jsonify({
            "usuarios": total_usuarios,
            "publicaciones": total_publicaciones,
            "reportes": total_reportes
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
