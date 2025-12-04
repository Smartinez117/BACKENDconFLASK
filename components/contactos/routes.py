from flask import Blueprint, request, jsonify, g
from core.models import Notificacion, Publicacion, SolicitudContacto, db
from auth.services import require_auth
from datetime import datetime, timezone 

# Eliminamos util y socketio
# from util import socketio 

contactos_bp = Blueprint("contactos", __name__)

@contactos_bp.route('/api/contactar', methods=['POST'])
@require_auth
def crear_solicitud():
    data = request.json
    usuario_actual = g.usuario_actual
    
    # 1. Validaciones
    pub = Publicacion.query.get(data['id_publicacion'])
    if not pub:
        return jsonify({'error': 'Publicación no encontrada'}), 404
    if pub.id_usuario == usuario_actual.id:
        return jsonify({'error': 'No puedes contactarte a ti mismo'}), 400

    # Verificar duplicados pendientes
    existente = SolicitudContacto.query.filter_by(
        id_solicitante=usuario_actual.id,
        id_publicacion=pub.id
    ).first()
    
    if existente and existente.estado == 0:
        return jsonify({'error': 'Ya tienes una solicitud pendiente'}), 400

    # Obtener datos
    tipo_contacto = data.get('tipo', 'whatsapp')
    mensaje_usuario = data.get('mensaje', '')

    # Determinar qué dato mostrar
    dato_contacto_mostrable = "No especificado"
    
    if tipo_contacto == 'whatsapp':
        if not usuario_actual.telefono_numero_local:
            return jsonify({'error': 'No tienes un número de teléfono configurado'}), 400
            
        dato_contacto_mostrable = f"{usuario_actual.telefono_pais or ''} {usuario_actual.telefono_numero_local}".strip()
    else:
        dato_contacto_mostrable = usuario_actual.email

    # 2. Crear la Solicitud
    nueva_solicitud = SolicitudContacto(
        id_solicitante=usuario_actual.id,
        id_receptor=pub.id_usuario,
        id_publicacion=pub.id,
        mensaje=mensaje_usuario,
        tipo_contacto=tipo_contacto
    )
    
    db.session.add(nueva_solicitud)
    db.session.flush() # Flush para obtener el ID antes del commit final

    # 3. Crear Notificación para el DUEÑO (Receptor)
    # Esto es lo que el Polling del dueño va a detectar en 15 segundos
    descripcion_noti = (
        f"{usuario_actual.nombre} quiere contactarte. "
        f"Dejó su {tipo_contacto.upper()}: {dato_contacto_mostrable}. "
        f"Mensaje: '{mensaje_usuario}'"
    )

    nueva_noti = Notificacion(
        id_usuario=pub.id_usuario, # Para el dueño
        titulo="Nueva solicitud de contacto",
        descripcion=descripcion_noti,
        tipo="solicitud_contacto", 
        id_publicacion=pub.id,
        id_referencia=nueva_solicitud.id, # Link a la solicitud para poder Aceptar/Rechazar
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
    
    # Seguridad: solo el dueño puede responder
    if solicitud.id_receptor != g.usuario_actual.id:
        return jsonify({'error': 'No autorizado'}), 403
        
    dato_contacto_solicitante_para_front = None

    if data['accion'] == 'aceptar':
        solicitud.estado = 1 # Aceptado
        
        # --- Recopilar Datos de Contacto ---
        
        # Datos del DUEÑO (Yo)
        tel_dueno = f"{g.usuario_actual.telefono_pais or ''} {g.usuario_actual.telefono_numero_local or ''}".strip()
        email_dueno = g.usuario_actual.email
        
        # Datos del SOLICITANTE (El otro)
        tel_solicitante = f"{solicitud.solicitante.telefono_pais or ''} {solicitud.solicitante.telefono_numero_local or ''}".strip()
        email_solicitante = solicitud.solicitante.email
        nombre_solicitante = solicitud.solicitante.nombre

        # Lógica de intercambio (si eligió whatsapp, le doy whatsapp, etc)
        dato_para_solicitante = tel_dueno if solicitud.tipo_contacto == 'whatsapp' else email_dueno
        dato_para_dueno = tel_solicitante if solicitud.tipo_contacto == 'whatsapp' else email_solicitante
        
        # Para el Toast inmediato del frontend
        dato_contacto_solicitante_para_front = dato_para_dueno

        # --- GENERAR NOTIFICACIONES PERSISTENTES ---

        # 1. Notificación para el SOLICITANTE (Feedback)
        # El Polling del solicitante detectará esto.
        noti_para_solicitante = Notificacion(
            id_usuario=solicitud.id_solicitante,
            titulo="¡Solicitud Aceptada!",
            descripcion=f"{g.usuario_actual.nombre} aceptó tu solicitud. Contacto: {dato_para_solicitante}",
            tipo="contacto_aceptado",
            id_publicacion=solicitud.id_publicacion,
            id_referencia=solicitud.id,
            fecha_creacion=datetime.now(timezone.utc)
        )
        db.session.add(noti_para_solicitante)

        # 2. Notificación para el DUEÑO (Historial)
        # Útil para que el dueño no pierda el número si cierra el popup
        noti_para_dueno = Notificacion(
            id_usuario=g.usuario_actual.id,
            titulo="Contacto realizado",
            descripcion=f"Aceptaste a {nombre_solicitante}. Su contacto es: {dato_para_dueno}",
            tipo="info_contacto",
            id_publicacion=solicitud.id_publicacion,
            id_referencia=solicitud.id,
            fecha_creacion=datetime.now(timezone.utc),
            leido=True # Nace leída porque él mismo hizo la acción
        )
        db.session.add(noti_para_dueno)
        
    elif data['accion'] == 'rechazar':
        solicitud.estado = 2 # Rechazado
        # Opcional: Crear notificación de "Tu solicitud fue rechazada" para el solicitante
        
    db.session.commit()

    # Eliminamos el bloque de socketio.emit
    
    return jsonify({
        'mensaje': 'Respuesta guardada', 
        'dato_contacto': dato_contacto_solicitante_para_front if data['accion']=='aceptar' else None,
        'tipo_contacto': solicitud.tipo_contacto
    })