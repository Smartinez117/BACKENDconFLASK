from flask import Blueprint, request, jsonify
from core.models import db, Usuario, Publicacion,Notificacion
from components.usuarios.services import (
    actualizar_datos_usuario,
    get_usuario,
    filtrar_usuarios_service,
    obtener_usuario_por_uid,
    obtener_usuario_por_slug,
)
from firebase_admin import auth
from auth.services import require_auth
from flask_socketio import SocketIO, disconnect
from util import socketio

usuarios_bp = Blueprint('usuarios', __name__)


#Endpoint para actualizar información del usuario
@usuarios_bp.route('/usuario/<int:id_usuario>', methods=['PATCH'])
def actualizar_usuario(id_usuario):
    '''Actualiza la información de un usuario existente.'''
    data = request.get_json()
    try:
        actualizar_datos_usuario(id_usuario,data)
        return jsonify({'mensaje': 'Usuario actualizado con éxito'}), 200
    except Exception as error:
        return jsonify({'error': str(error)}), 400

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


@usuarios_bp.route('/usuario/<int:id_usuario>', methods=['DELETE'])
def eliminar_usuario(id_usuario):
    '''Elimina un usuario por su ID.'''
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    db.session.delete(usuario)
    db.session.commit()

    return jsonify({'mensaje': f'Usuario {usuario.nombre} eliminado correctamente'}), 200


#endpoint para obtener los datos de un usuario por el uid
# (usando en la interface de configuraciones de perfil)
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



#diccionario de usuarios conectados
userconnected = {}
sid_uid_map={}
#funcion para autenticar a los usuarios desde el socket
@socketio.on('connect', namespace='/connection')
def on_connect(auth_data):
    print("NAMESPACE:", request.namespace)
    print("clave solucion funcional")

    '''Autentica al usuario que se conecta al socket usando el token de Firebase.'''
    token = auth_data.get('token') if auth_data else None
    if not token:
        disconnect()
        return

    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token.get('uid')
        name= decoded_token.get('name')
        sid = request.sid #<-- identificador unico de inicio de sesion del socket
        # para cada conexion de cada user
        print(uid,name,sid)
        if not uid:
            disconnect()
            return
        usuario_conectado(uid,name,sid)
        from components.notificaciones.services import notificarconectado
        id_user= obtener_usuario_por_uid(uid).id
        #notificarconectado(id_user,uid)  <---- solo falta descomentar esto y ya funcionaria o bueno probarlo mas bien
    except Exception:
        disconnect()

#marcar como desconectado a los usuarios que se desconectan
@socketio.on('disconnect', namespace='/connection')
def on_disconnect():
    '''Marca al usuario como desconectado cuando se desconecta del socket.'''
    sid = request.sid
    print("clave")
   # uid = sid_uid_map.get(sid)
    if sid not in sid_uid_map:
        print("ingorno disconection")
        return
    uid= sid_uid_map.pop(sid)
    if uid is None:
        print("Desconexión ignorada (SID no registrado)", sid)
        return
   # eliminar el SID
    #sid_uid_map.pop(sid, None)
    if userconnected.get(uid, {}).get("sid") == sid:
     usuario_desconectado(uid)

#agrego a cada user con su uid,name y sid a un diccionario de user connected
def usuario_conectado(uid,name,sid):
    '''Agrega un usuario al diccionario de usuarios conectados.'''
    userconnected[uid]= {
        "sid": sid,
        "name": name
        }
    print('usuarios conectados:',userconnected)
    sid_uid_map[sid]=uid


def usuario_desconectado(uid):
    '''Elimina un usuario del diccionario de usuarios conectados.'''
    #userconnected.pop(uid,None)
    print('usuarios conectados(FD):',userconnected)

# Endpoint para obtener publicaciones de un usuario por su id
#idUsuario : es el id traido desde el endpoint
#id_usuario : es un atributo de cada publicacion, se ven parecidos pero la diferencia esta en el guión bajo
@usuarios_bp.route('/usuarios/<int:idUsuario>/publicaciones', methods=['GET'])
def obtener_publicaciones_usuario(idUsuario):
    '''Obtiene todas las publicaciones de un usuario específico por su ID.'''
    try:
        publicaciones = (
            Publicacion.query.filter_by(id_usuario=idUsuario)
            .order_by(Publicacion.id.desc())
            .all()
        )

        return jsonify([pub.to_dict() for pub in publicaciones]), 200
    except Exception as error:
        return jsonify({'error': str(error)}), 400


# Endpoint para verificar si un usuario es admin (role_id == 2)
@usuarios_bp.route('/usuario/<string:uid>/is_admin', methods=['GET'])
def es_admin(uid):
    """Devuelve si el usuario con `uid` (firebase_uid) es administrador.

    Respuesta JSON: { 'is_admin': true/false } o error si no existe el usuario.
    """
    # Obtener el usuario directamente desde la base de datos como modelo
    usuario = Usuario.query.filter_by(firebase_uid=uid).first()

    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    # `role_id` almacena el id del rol; 2 == admin
    is_admin = (getattr(usuario, 'role_id', None) == 2)


    return jsonify({'is_admin': bool(is_admin)}), 200
    


