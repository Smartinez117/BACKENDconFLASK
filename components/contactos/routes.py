from flask import Blueprint, request, jsonify, g
from core.models import Notificacion, Publicacion, SolicitudContacto, db
from auth.services import require_auth
from datetime import datetime, timezone # <--- 1. AGREGAR ESTE IMPORT

contactos_bp = Blueprint("contactos", __name__)

@contactos_bp.route('/api/contactar', methods=['POST'])
@require_auth
def crear_solicitud():
    data = request.json
    usuario_actual = g.usuario_actual
    
    # Validar que no se auto-contacte
    pub = Publicacion.query.get(data['id_publicacion'])
    if not pub:
        return jsonify({'error': 'Publicación no encontrada'}), 404

    if pub.id_usuario == usuario_actual.id:
        return jsonify({'error': 'No puedes contactarte a ti mismo'}), 400

    # Verificar si ya existe una solicitud pendiente
    existente = SolicitudContacto.query.filter_by(
        id_solicitante=usuario_actual.id,
        id_publicacion=pub.id
    ).first()
    
    if existente and existente.estado == 0:
        return jsonify({'error': 'Ya tienes una solicitud pendiente para esta publicación'}), 400

    # Recibir el tipo de contacto
    tipo_contacto = data.get('tipo', 'whatsapp')

    nueva_solicitud = SolicitudContacto(
        id_solicitante=usuario_actual.id,
        id_receptor=pub.id_usuario,
        id_publicacion=pub.id,
        mensaje=data.get('mensaje', 'Hola, quiero contactarte por tu publicación.'),
        tipo_contacto=tipo_contacto
    )
    
    db.session.add(nueva_solicitud)
    db.session.flush() 

    # Crear Notificación para el dueño
    nueva_noti = Notificacion(
        id_usuario=pub.id_usuario,
        titulo="Nueva solicitud de contacto",
        descripcion=f"{usuario_actual.nombre} quiere contactarte vía {tipo_contacto.upper()}: '{data.get('mensaje')}'",
        tipo="solicitud_contacto", 
        id_publicacion=pub.id,
        id_referencia=nueva_solicitud.id,
        
        # --- 2. CORRECCIÓN AQUÍ: AGREGAR LA FECHA ---
        fecha_creacion=datetime.now(timezone.utc) 
    )
    db.session.add(nueva_noti)
    
    db.session.commit()
    
    return jsonify({'mensaje': 'Solicitud enviada'}), 201


@contactos_bp.route('/api/contactar/<int:id_solicitud>/responder', methods=['PATCH'])
@require_auth
def responder_solicitud(id_solicitud):
    data = request.json 
    solicitud = SolicitudContacto.query.get_or_404(id_solicitud)
    
    if solicitud.id_receptor != g.usuario_actual.id:
        return jsonify({'error': 'No autorizado'}), 403
        
    dato_contacto_solicitante = None

    if data['accion'] == 'aceptar':
        solicitud.estado = 1
        
        dato_dueno = ""
        mensaje_noti = ""

        if solicitud.tipo_contacto == 'whatsapp':
            dato_dueno = f"{g.usuario_actual.telefono_pais or ''} {g.usuario_actual.telefono_numero_local or ''}".strip()
            mensaje_noti = f"{g.usuario_actual.nombre} aceptó tu solicitud. Su WhatsApp es: {dato_dueno}"
            dato_contacto_solicitante = f"{solicitud.solicitante.telefono_pais or ''} {solicitud.solicitante.telefono_numero_local or ''}".strip()
        
        elif solicitud.tipo_contacto == 'email':
            dato_dueno = g.usuario_actual.email
            mensaje_noti = f"{g.usuario_actual.nombre} aceptó tu solicitud. Su Email es: {dato_dueno}"
            dato_contacto_solicitante = solicitud.solicitante.email
        
        else:
            dato_dueno = "Consulta su perfil para ver los datos."
            mensaje_noti = f"{g.usuario_actual.nombre} aceptó tu solicitud."

        # Notificación de respuesta (También necesita fecha)
        noti_aceptada = Notificacion(
            id_usuario=solicitud.id_solicitante,
            titulo="¡Solicitud Aceptada!",
            descripcion=mensaje_noti,
            tipo="contacto_aceptado",
            id_publicacion=solicitud.id_publicacion,
            id_referencia=solicitud.id,
            
            # --- CORRECCIÓN AQUÍ TAMBIÉN ---
            fecha_creacion=datetime.now(timezone.utc)
        )
        db.session.add(noti_aceptada)
        
    elif data['accion'] == 'rechazar':
        solicitud.estado = 2
        
    db.session.commit()
    
    return jsonify({
        'mensaje': 'Respuesta guardada', 
        'dato_contacto': dato_contacto_solicitante if data['accion']=='aceptar' else None,
        'tipo_contacto': solicitud.tipo_contacto
    })