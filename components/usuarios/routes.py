from flask import Blueprint, request, jsonify
from core.models import db, Usuario
from components.usuarios.services import actualizar_datos_usuario , get_usuario,filtrar_usuarios_service, obtener_usuario_por_uid, obtener_usuario_por_slug
from firebase_admin import auth 
from auth.services import require_auth
from flask_socketio import SocketIO, disconnect
from util import socketio
from core.models import db, Publicacion  # importa tu modelo de publicaciones

usuarios_bp = Blueprint('usuarios', __name__)


#Endpoint para actualizar información del usuario
@usuarios_bp.route('/usuario/<int:id_usuario>', methods=['PATCH'])
def actualizar_usuario(id_usuario):
    '''Actualiza la información de un usuario existente.'''
    data = request.get_json()
    try:
        actualizar_datos_usuario(id_usuario,data)
        return jsonify({'mensaje': 'Usuario actualizado con éxito'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

#Endpoint para obtener usuarios por su id
@usuarios_bp.route('/usuario/<int:id_usuario>', methods = ['GET'])
def obtener_usuario_por_id(id_usuario):
    '''Obtiene la información de un usuario por su ID.'''
    usuario = get_usuario(id_usuario) 
    return jsonify(usuario), 200

# Endpoint para obtener usuario por slug
@usuarios_bp.route('/usuario/slug/<string:slug>', methods=['GET'])
def obtener_usuario_por_slug_route(slug):
    '''Obtiene la información de un usuario por su slug.'''
    usuario = obtener_usuario_por_slug(slug)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    return jsonify(usuario), 200

#Endpoint para poder banear usuarios
@usuarios_bp.route('/api/<int:id_usuario>/ban', methods=['PATCH'])
@require_auth
def banear_usuario(id_usuario):
    '''Busca un usuario por su ID y lo banea si no es admin.'''
    usuario = Usuario.query.get_or_404(id_usuario)

    if usuario.rol == "admin":
        return jsonify({"error": "No se puede banear a otro administrador"}), 403

    try:
        # Deshabilitar el usuario en Firebase
        auth.update_user(usuario.firebase_uid, disabled=True)
        usuario.rol = "baneado"
        db.session.commit()

        return jsonify({"mensaje": f"Usuario {usuario.nombre} baneado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": f"No se pudo banear al usuario: {str(e)}"}), 500

#Endpoint para desbanear usuarios
@usuarios_bp.route('/api/<int:id_usuario>/desban', methods=['PATCH'])
@require_auth
def desbanear_usuario(id_usuario):
    '''Busca un usuario por su ID y lo desbanea si no es admin.'''
    # Buscar usuario en tu base de datos
    usuario = Usuario.query.get_or_404(id_usuario)

    # Si ya es admin, no debería estar baneado pero controlamos igual
    if usuario.rol == "admin":
        return jsonify({"error": "Los administradores no pueden ser baneados/desbaneados"}), 403

    try:
        # Rehabilitar al usuario en Firebase
        auth.update_user(usuario.firebase_uid, disabled=False)

        # Actualizar el rol en tu DB local
        usuario.rol = "usuario"
        db.session.commit()

        return jsonify({"mensaje": f"Usuario {usuario.nombre} desbaneado correctamente"}), 200

    except Exception as e:
        return jsonify({"error": f"No se pudo desbanear al usuario: {str(e)}"}), 500

@usuarios_bp.route('/usuario/<int:id_usuario>', methods=['DELETE'])
def eliminar_usuario(id_usuario):
    '''Elimina un usuario por su ID.'''
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    db.session.delete(usuario)
    db.session.commit()

    return jsonify({'mensaje': f'Usuario {usuario.nombre} eliminado correctamente'}), 200


#endpoint para obtener los datos de un usuario por el uid (usando en la interface de configuraciones de perfil)
@usuarios_bp.route('/api/userconfig', methods=['GET'])
def user_config():
    '''Obtiene los datos completos del usuario autenticado usando su token Firebase.'''
    auth_header = request.headers.get('Authorization', '')

    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token no proporcionado o malformado'}), 401

    id_token = auth_header.split('Bearer ')[1]

    try:
        # Validar token y extraer uid
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token.get('uid')

        if not uid:
            return jsonify({'error': 'Token inválido, sin uid'}), 401

        # Buscar usuario por uid
        usuario = obtener_usuario_por_uid(uid)
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Devolver datos completos del usuario
        return jsonify(usuario), 200

    except Exception as e:
        return jsonify({'error': 'Token inválido o expirado', 'detalle': str(e)}), 401

#Endpoints para el panel administrativo:

@usuarios_bp.route("/api/usuarios", methods=["GET"])
def get_usuarios():
    ''' Obtiene una lista paginada de usuarios, con opción de búsqueda por nombre o email.'''
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    search = request.args.get("search", "", type=str)

    query = Usuario.query

    if search:
        query = query.filter(
            (Usuario.nombre.ilike(f"%{search}%")) |
            (Usuario.email.ilike(f"%{search}%"))
        )

    pagination = query.order_by(Usuario.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    data = [u.to_dict() for u in pagination.items]

    return jsonify({
        "usuarios": data,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages
    })

#Endpoint para filtrar usuarios por mail, nombre , telefono y rol
"""@usuarios_bp.route('/api/usuarios', methods=['GET'])
def filtrar_usuarios():
    filtros = {
        "email": request.args.get('email'),
        "nombre": request.args.get('nombre'),
        "telefono_pais": request.args.get('telefono_pais'),
        "telefono_numero_local": request.args.get('telefono_numero_local'),
        "rol": request.args.get('rol')
    }

    try:
        usuarios_filtrados = filtrar_usuarios_service(filtros)
        return jsonify(usuarios_filtrados), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400"""

#diccionario de usuarios conectados
userconnected = {}

#funcion para autenticar a los usuarios desde el socket
@socketio.on('connect', namespace='/connection')
def on_connect(auth_data):
    '''Autentica al usuario que se conecta al socket usando el token de Firebase.'''
    token = auth_data.get('token') if auth_data else None
    if not token:
        disconnect()
        return

    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token.get('uid')
        name= decoded_token.get('name')
        sid = request.sid #<-- identificador unico de inicio de sesion del socket para cada conexion de cada user
        print(uid,name,sid)
        if not uid:
            disconnect()
            return
        usuario_conectado(uid,name,sid)
    except Exception:
        disconnect()

#marcar como desconectado a los usuarios que se desconectan
@socketio.on('disconnect', namespace='/connection')
def on_disconnect():
    '''Marca al usuario como desconectado cuando se desconecta del socket.'''
    sid = request.sid
    usuario_desconectado(sid)

#agrego a cada user con su uid,name y sid a un diccionario de user connected
def usuario_conectado(uid,name,sid):
    '''Agrega un usuario al diccionario de usuarios conectados.'''
    userconnected[sid]= {
        "uid": uid,
        "name": name
        }
    print('usuarios conectados:',userconnected)


def usuario_desconectado(sid):
    '''Elimina un usuario del diccionario de usuarios conectados.'''
    userconnected.pop(sid,None)
    print('usuarios conectados:',userconnected)




# Endpoint para obtener publicaciones de un usuario por su id
@usuarios_bp.route('/usuarios/<int:idUsuario>/publicaciones', methods=['GET'])
def obtener_publicaciones_usuario(id_usuario):
    '''Obtiene todas las publicaciones de un usuario específico por su ID.'''
    try:
        usuario = Usuario.query.get_or_404(id_usuario)

        publicaciones = (
            Publicacion.query.filter_by(id_usuario=id_usuario)
            .order_by(Publicacion.id.desc())
            .all()
        )

        return jsonify([pub.to_dict() for pub in publicaciones]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
