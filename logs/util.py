import time
from flask import g
from core.models import db, RequestLog
import requests
import cloudinary.uploader
from supabase import create_client
import functools
import time
import datetime
import uuid
from flask import g, request
from core.models import db, RequestLog  # Asegurate que el modelo esté bien importado


def crear_log(origen, endpoint, tiempo_respuesta, exito=True, mensaje=None, id_usuario=None):
    """Crea y guarda un log en la base de datos."""
    nuevo_log = Log(
        origen=origen,
        endpoint=endpoint,
        tiempo_respuesta=tiempo_respuesta,
        exito=exito,
        mensaje=mensaje,
        id_usuario=id_usuario
    )
    db.session.add(nuevo_log)
    db.session.commit()



def log_external(origen):
    """Decorator para medir tiempo y loguear requests a servicios externos"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            inicio = time.time()
            id_usuario = kwargs.get("id_usuario")
            try:
                result = func(*args, **kwargs)  # llamamos a la función real
                duracion = (time.time() - inicio) * 1000
                crear_log(origen, func.__name__, duracion, exito=True, id_usuario=id_usuario)
                return result
            except Exception as e:
                duracion = (time.time() - inicio) * 1000
                crear_log(origen, func.__name__, duracion, exito=False, mensaje=str(e), id_usuario=id_usuario)
                raise
        return wrapper
    return decorator


def before_request_log():
    """Hook para guardar el tiempo de llegada de la request."""
    g.request_id = str(uuid.uuid4())
    g.timestamp_arrival = datetime.datetime.now(datetime.timezone.utc)

def after_request_log(response):
    """Hook para guardar el tiempo de respuesta y crear el log."""
    log = RequestLog(
        request_id=g.get('request_id'),
        path=request.path,
        method=request.method,
        timestamp_arrival=g.get('timestamp_arrival'),
        timestamp_send_supabase=g.get('timestamp_send_supabase'),
        timestamp_return_supabase=g.get('timestamp_return_supabase'),
        timestamp_send_cloudinary=g.get('timestamp_send_cloudinary'),
        timestamp_return_cloudinary=g.get('timestamp_return_cloudinary'),
        timestamp_send_firebase=g.get('timestamp_send_firebase'),
        timestamp_return_firebase=g.get('timestamp_return_firebase'),
        timestamp_response_sent=datetime.datetime.now(datetime.timezone.utc),
        status_code=response.status_code,
    )
    db.session.add(log)
    db.session.commit()
    return response