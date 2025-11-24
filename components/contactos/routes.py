from flask import Blueprint, request, jsonify, g
from core.models import Notificacion, Publicacion, SolicitudContacto, db
from auth.services import require_auth
from datetime import datetime, timezone 
from util import socketio 

contactos_bp = Blueprint("contactos", __name__)

@contactos_bp.route('/api/contactar', methods=['POST'])
@require_auth
def crear_solicitud():
    data = request.json
    usuario_actual = g.usuario_actual
    
    # Validaciones básicas
    pub = Publicacion.query.get(data['id_publicacion'])
    if not pub:
        return jsonify({'error': 'Publicación no encontrada'}), 404
    if pub.id_usuario == usuario_actual.id:
        return jsonify({'error': 'No puedes contactarte a ti mismo'}), 400

    # Verificar si ya existe solicitud pendiente
    existente = SolicitudContacto.query.filter_by(
        id_solicitante=usuario_actual.id,
        id_publicacion=pub.id
    ).first()
    if existente and existente.estado == 0:
        return jsonify({'error': 'Ya tienes una solicitud pendiente'}), 400

    # Obtener tipo y mensaje
    tipo_contacto = data.get('tipo', 'whatsapp')
    mensaje_usuario = data.get('mensaje', '')

    # --- CAMBIO: Obtener el dato de contacto del solicitante AHORA ---
    dato_contacto_mostrable = "No especificado"
    
    if tipo_contacto == 'whatsapp':
        # Validar que tenga teléfono cargado
        if not usuario_actual.telefono_numero_local:
            return jsonify({'error': 'No tienes un número de teléfono configurado en tu perfil'}), 400
            
        dato_contacto_mostrable = f"{usuario_actual.telefono_pais or ''} {usuario_actual.telefono_numero_local}".strip()
    else:
        dato_contacto_mostrable = usuario_actual.email

    # Creamos la solicitud
    nueva_solicitud = SolicitudContacto(
        id_solicitante=usuario_actual.id,
        id_receptor=pub.id_usuario,
        id_publicacion=pub.id,
        mensaje=mensaje_usuario,
        tipo_contacto=tipo_contacto
    )
    
    db.session.add(nueva_solicitud)
    db.session.flush() 

    # --- CAMBIO: Incluimos el contacto explícitamente en la descripción ---
    descripcion_noti = (
        f"{usuario_actual.nombre} quiere contactarte. "
        f"Dejó su {tipo_contacto.upper()}: {dato_contacto_mostrable}. "
        f"Mensaje: '{mensaje_usuario}'"
    )

    nueva_noti = Notificacion(
        id_usuario=pub.id_usuario,
        titulo="Nueva solicitud de contacto",
        descripcion=descripcion_noti, # <--- Aquí va el dato visible
        tipo="solicitud_contacto", 
        id_publicacion=pub.id,
        id_referencia=nueva_solicitud.id,
        fecha_creacion=datetime.now(timezone.utc)
    )
    db.session.add(nueva_noti)
    
    db.session.commit()
    
    return jsonify({'mensaje': 'Solicitud enviada con tus datos'}), 201


@contactos_bp.route('/api/contactar/<int:id_solicitud>/responder', methods=['PATCH'])
@require_auth
def responder_solicitud(id_solicitud):
    data = request.json 
    solicitud = SolicitudContacto.query.get_or_404(id_solicitud)
    
    if solicitud.id_receptor != g.usuario_actual.id:
        return jsonify({'error': 'No autorizado'}), 403
        
    dato_contacto_solicitante_para_front = None

    if data['accion'] == 'aceptar':
        solicitud.estado = 1
        
        # 1. Preparamos los datos de AMBOS
        
        # Datos del DUEÑO (Actual usuario)
        tel_dueno = f"{g.usuario_actual.telefono_pais or ''} {g.usuario_actual.telefono_numero_local or ''}".strip()
        email_dueno = g.usuario_actual.email
        
        # Datos del SOLICITANTE (El que mandó la solicitud)
        tel_solicitante = f"{solicitud.solicitante.telefono_pais or ''} {solicitud.solicitante.telefono_numero_local or ''}".strip()
        email_solicitante = solicitud.solicitante.email
        nombre_solicitante = solicitud.solicitante.nombre

        # Definimos qué dato mostrar según el tipo
        dato_para_solicitante = tel_dueno if solicitud.tipo_contacto == 'whatsapp' else email_dueno
        dato_para_dueno = tel_solicitante if solicitud.tipo_contacto == 'whatsapp' else email_solicitante
        
        # Esto es lo que el frontend mostrará en el Toast inmediato
        dato_contacto_solicitante_para_front = dato_para_dueno

        # ---------------------------------------------------------
        # 2. CREACIÓN DE NOTIFICACIONES (GUARDAR EN BASE DE DATOS)
        # ---------------------------------------------------------

        # A) Notificación para el SOLICITANTE (Le llega el dato del dueño)
        noti_para_solicitante = Notificacion(
            id_usuario=solicitud.id_solicitante, # Destino: Solicitante
            titulo="¡Solicitud Aceptada!",
            descripcion=f"{g.usuario_actual.nombre} aceptó tu solicitud. Contacto: {dato_para_solicitante}",
            tipo="contacto_aceptado",
            id_publicacion=solicitud.id_publicacion,
            id_referencia=solicitud.id,
            fecha_creacion=datetime.now(timezone.utc)
        )
        db.session.add(noti_para_solicitante)

        # B) NUEVO: Notificación para el DUEÑO (Autonotificación para guardar el dato)
        # Así, si cierra el toast, puede ir a 'Notificaciones' y ver el número de nuevo.
        noti_para_dueno = Notificacion(
            id_usuario=g.usuario_actual.id, # Destino: Dueño (Yo mismo)
            titulo="Contacto realizado",
            descripcion=f"Aceptaste a {nombre_solicitante}. Su contacto es: {dato_para_dueno}",
            tipo="info_contacto", # Tipo informativo, no requiere acción
            id_publicacion=solicitud.id_publicacion,
            id_referencia=solicitud.id,
            fecha_creacion=datetime.now(timezone.utc),
            leido=True # Podemos marcarla como leída porque la acaba de generar él mismo
        )
        db.session.add(noti_para_dueno)
        
    elif data['accion'] == 'rechazar':
        solicitud.estado = 2
        # Opcional: Notificar rechazo al solicitante
        
    db.session.commit()

    # 3. SOCKETS (Opcional pero recomendado para que aparezca al instante)
    # Avisar al solicitante que fue aceptado
    if data['accion'] == 'aceptar':
         try:
            socketio.emit(
                'nueva_notificacion', 
                {"mensaje": "Tu solicitud fue aceptada"}, 
                room=solicitud.solicitante.firebase_uid, # Asegúrate de usar el ID correcto para el room
                namespace='/notificacion'
            )
         except Exception as e:
            print(f"Error socket: {e}")

    
    return jsonify({
        'mensaje': 'Respuesta guardada', 
        'dato_contacto': dato_contacto_solicitante_para_front if data['accion']=='aceptar' else None,
        'tipo_contacto': solicitud.tipo_contacto
    })