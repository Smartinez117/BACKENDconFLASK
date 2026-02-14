from flask import Blueprint, request, jsonify
from .services import obtener_roles, crear_rol, actualizar_rol, eliminar_rol

roles_bp = Blueprint("roles", __name__)


@roles_bp.route("/api/roles", methods=["GET"])
def listar_roles():
    roles = obtener_roles()
    return jsonify(roles), 200


@roles_bp.route("/api/roles", methods=["POST"])
def nuevo_rol():
    data = request.get_json()
    nombre = data.get("nombre")
    if not nombre:
        return jsonify({"error": "El nombre es obligatorio"}), 400

    rol = crear_rol(nombre)
    if rol:
        return jsonify(rol), 201
    return jsonify({"error": "No se pudo crear el rol"}), 500


@roles_bp.route("/api/roles/<int:id>", methods=["PUT"])
def editar_rol(id):
    data = request.get_json()
    nombre = data.get("nombre")
    if not nombre:
        return jsonify({"error": "El nombre es obligatorio"}), 400

    rol = actualizar_rol(id, nombre)
    if rol:
        return jsonify(rol), 200
    return jsonify({"error": "Rol no encontrado"}), 404


@roles_bp.route("/api/roles/<int:id>", methods=["DELETE"])
def borrar_rol(id):
    ok = eliminar_rol(id)
    if ok:
        return jsonify({"message": "Rol eliminado correctamente"}), 200
    return jsonify({"error": "Rol no encontrado"}), 404
