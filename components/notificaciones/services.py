from core.models import db, Notificacion,Publicacion
from datetime import datetime,timezone
#from routes import userconnected
from ..usuarios.routes import userconnected  #importamos la libreria de usuarios conectados
from util import socketio
from ..usuarios.services import get_usuario
from flask_socketio import join_room,leave_room,emit
import pytz
zona_arg = pytz.timezone("America/Argentina/Buenos_Aires")

def crear_notificacion(data):#suponog que aca habria que agregar lo del id de la publicacion
    """Crea una nueva notificación en la base de datos."""
    print("se ejecuto la funcion de notificaciones")
    try:
        nueva = Notificacion(
            id_usuario=data['id_usuario'],
            titulo=data.get('titulo'),
            descripcion=data.get('descripcion'),
            tipo=data.get('tipo'),
            fecha_creacion=datetime.now(timezone.utc),
            leido=False,
            id_publicacion=data.get('id_publicacion')
        )
        db.session.add(nueva)
        db.session.commit()
        print("pre notificcacioin")
        notificar(nueva)
        print("debio ejecutrase la funcion de notificar con los sockets")
    
        return {"mensaje": "Notificación creada", "id": nueva.id}, 201
        
    except Exception as error:
        db.session.rollback()
        return {"error": str(error)}, 400


def obtener_notificaciones_por_usuario(id_usuario, solo_no_leidas=False):
    query = Notificacion.query.filter_by(id_usuario=id_usuario)
    
    if solo_no_leidas:
        query = query.filter_by(leido=False)
        
    notificaciones = query.order_by(Notificacion.fecha_creacion.desc()).limit(50).all()
    
    # Opción A: Usar el método to_dict() del modelo (Recomendado)
    return [n.to_dict() for n in notificaciones]


def obtener_todas():
    """Obtiene todas las notificaciones de la base de datos."""
    query = Notificacion.query.order_by(Notificacion.fecha_creacion.desc()).all()
    return [noti_to_dict(n) for n in query]


def marcar_notificacion_como_leida(id_noti):
    """Marca una notificación como leída por su ID."""
    noti = Notificacion.query.get(id_noti)
    if not noti:
        return {"error": "No encontrada"}, 404
    noti.leido = True
    db.session.commit()
    return {"mensaje": "Notificación marcada como leída"}



def eliminar_notificacion(id_noti):
    """Elimina una notificación de la base de datos por su ID."""
    noti = Notificacion.query.get(id_noti)
    if not noti:
        return {"error": "No encontrada"}, 404
    db.session.delete(noti)
    db.session.commit()
    return {"mensaje": "Notificación eliminada"}


def noti_to_dict(notificacion):
    """Convierte una notificación a un diccionario serializable."""
    ahora = datetime.now(timezone.utc)
    delta = ahora - notificacion.fecha_creacion

    if delta.days > 0:
        tiempo_pasado = f"hace {delta.days} día(s)"
    elif delta.seconds >= 3600:
        tiempo_pasado = f"hace {delta.seconds // 3600} hora(s)"
    elif delta.seconds >= 60:
        tiempo_pasado = f"hace {delta.seconds // 60} minuto(s)"
    else:
        tiempo_pasado = "hace unos segundos"

    return {
        "id": notificacion.id,
        "id_usuario": notificacion.id_usuario,
        "id_publicacion":notificacion.id_publicacion,
        "titulo": notificacion.titulo,
        "descripcion": notificacion.descripcion,
        "tipo": notificacion.tipo,
        "fecha_creacion": notificacion.fecha_creacion.isoformat(),
        "tiempo_pasado": tiempo_pasado,
        "leido": notificacion.leido
    }

#funciones para las notficaiones de los sockets
#aqui voy a definir dos eventos que creo que son los unicos asique vamos a verlos despues

#en caso de que ocurra el evento de que alguien comenta tu publicacion entonces notifica inmediato
#iria de la mano con la funcion de crear notificacion asique la dejare aqui notado
def notificar(newnotificacion):
    """Envía una notificación en tiempo real al usuario correspondiente usando sockets."""
    id_owner = obtener_user_por_idpublicacion(newnotificacion.id_publicacion)
    user = get_usuario(id_owner)
    uid_user= user["firebase_uid"]
    if  uid_user in userconnected:  
        print("entro a la bifurcacion")   
        notification = {
            "titulo": newnotificacion.titulo,
            "descripcion": newnotificacion.descripcion,
            "id_publicacion" :newnotificacion.id_publicacion, # para redirigir al user a la publicacion
            "id_notificacion": newnotificacion.id  #para marcarla como leida
        }
        socketio.emit('notificacion',notification,room=uid_user,namespace='/notificacion')

#en caso de que te conectes entonces le pides al back todas tus notificaciones:
#esta la tendria que importar en la parte que cree para registrar a los user en la carpeta de users
#voy a reutilizar las funciones que ya estand definidas
def notificarconectado(iduser,uid_user):
    """Envía todas las notificaciones pendientes a un usuario conectado."""
    notificaciones_pendientes = obtener_notificaciones_por_usuario(iduser)
    if notificaciones_pendientes and uid_user in userconnected:
        for notification in notificaciones_pendientes:
            socketio.emit('notificacion',notification,room=uid_user,namespace='/notificacion') 
#esta va a enviar todas las notificaciones pendientes que tiene la cosa incluso
#podemos enviarlas en orden soo modificando el query

def obtener_user_por_idpublicacion(publicacion_id):
    """Obtiene el ID de usuario dueño de una publicación dado el ID de la publicación."""
    publicacion = Publicacion.query.get(publicacion_id)
    if publicacion:
        return publicacion.id_usuario

###------------------------FUNCIONAMIENTO DEL CHAT------------------------#################
USER_ROOMS={}
CHAT_ROOMS={}
#iniciar conversaciones entre users
def iniciar_conversacion(uid,roomID):
    CHAT_ROOMS[roomID]={
        'users':[uid],
        'mensajes':[],
        'last_m_user1':0,
        'last_m_user2':0
    }
    if uid not in USER_ROOMS:
        USER_ROOMS[uid]=[]
    USER_ROOMS[uid].append(roomID)
    if roomID not in USER_ROOMS[uid]:  
        USER_ROOMS[uid].append(roomID)

#guardar los mensajes que se envien 
def guardar_mensaje(roomID,uid_sender,mensaje):
   if roomID in CHAT_ROOMS:
    CHAT_ROOMS[roomID]['mensajes'].append({
       uid_sender:mensaje
    })

def solicitud_mensaje(uid):
    socketio.emit('solicitud','alguien te envio un mensaje privado',namespace='/solicitud_CHAT/'+uid) 

#decorardores de evnetos para los sockets 
#socket que escucha cuando uno se une a un chat y lo guarda 
@socketio.on('join_chat')
def handle_join_chat(data):
    room = data['room'] 
    uid_user = data.get('user')
    user_notificar = data.get ('usuario2')
    join_room(room)  # Une este socket al room
    iniciar_conversacion(uid_user,room)
    solicitud_mensaje(user_notificar) # aqui le notificamos al otro que se le envio un mensaje
    emit('status', f'{uid_user} se unió al chat {room}', room=room)
# aqui el user que quiere la conversacion crea un room con su uID cosa que despues el otro user se conecte

@socketio.on('send_message')
def handle_send_message(data):
    user_uid= data.get('uid_user')
    room = data.get('room')
    message = data.get('menssage')
    guardar_mensaje(room,user_uid,message)
    emit('message', message, to=room)

@socketio.on('leave_chat')
def handle_leave_chat(data):
    room = data['room']
    user = data.get('user')
    leave_room(room)
    emit('status', f'{user} salió del chat {room}', room=room)

#para unirse desde el front se usa:

#socket.emit('join_chat', { room: 'uid', user1: 'usuario1',user_not:'usuario2' }); se puede usar los uid de cada user para generar los rooms 
#lo que vamos a enviar sera el uid del que quiere enviar mensaje y el uid o cualquier dato que sirva para identificar a quien le enviamos el mensaje 

#para enviar un mensaje desde el front usar:
#Para emitir otro evento, por ejemplo 'send_message' con datos
#socket.emit('send_message', { room: 'chat123', message: 'Hola, ¿cómo estás?',uid_user= '1234567asdasd' });
def enviar_mensajes_pendientes(uid):
    """Envía todos los mensajes pendientes guardados en memory a un usuario conectado."""

    # Verificas que el usuario esté conectado y tienes su sid
    if uid in userconnected:
        sid = userconnected[uid]['sid']
        
        # Buscar todos los rooms del usuario
        rooms_usuario = USER_ROOMS.get(uid, [])
        
        # Por cada room obtener mensajes pendientes
        for room in rooms_usuario:
            if room in CHAT_ROOMS:
                mensajes = CHAT_ROOMS[room]['mensajes']
                for mensaje in mensajes:
                    socketio.emit('mensaje', mensaje, room=sid)

#notas de desarrollo:
#para la parte del evento de recibir todo apenas se conecte debe funcionar agregando las fucniones cuando apenas se conecte el user:
# sera la primera version del chat con respecto al back
###------------------------FUNCIONAMIENTO DEL CHAT------------------------#################