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


def crear_log(
    request_id,
    path,
    method,
    timestamp_arrival=None,
    timestamp_start_processing=None,
    timestamp_send_supabase=None,
    timestamp_return_supabase=None,
    timestamp_send_cloudinary=None,
    timestamp_return_cloudinary=None,
    timestamp_send_firebase=None,
    timestamp_return_firebase=None,
    timestamp_response_sent=None,
    worker_id=None,
    request_type=None,
    payload_size=None,
    image_size=None,
    status_code=None,
    error=None
):
    """Crea y guarda un log en la base de datos."""
    nuevo_log = RequestLog(
        request_id=request_id,
        path=path,
        method=method,
        timestamp_arrival=timestamp_arrival,
        timestamp_start_processing=timestamp_start_processing,
        timestamp_send_supabase=timestamp_send_supabase,
        timestamp_return_supabase=timestamp_return_supabase,
        timestamp_send_cloudinary=timestamp_send_cloudinary,
        timestamp_return_cloudinary=timestamp_return_cloudinary,
        timestamp_send_firebase=timestamp_send_firebase,
        timestamp_return_firebase=timestamp_return_firebase,
        timestamp_response_sent=timestamp_response_sent,
        worker_id=worker_id,
        request_type=request_type,
        payload_size=payload_size,
        image_size=image_size,
        status_code=status_code,
        error=error
    )
    db.session.add(nuevo_log)
    db.session.commit()



def log_external(origen):
    """Decorator para medir y guardar timestamps de requests a servicios externos en g."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = datetime.datetime.now(datetime.timezone.utc)
            if origen == "firebase":
                g.timestamp_send_firebase = now
            elif origen == "cloudinary":
                g.timestamp_send_cloudinary = now
            elif origen == "supabase":
                g.timestamp_send_supabase = now
            try:
                result = func(*args, **kwargs)
                now_return = datetime.datetime.now(datetime.timezone.utc)
                if origen == "firebase":
                    g.timestamp_return_firebase = now_return
                elif origen == "cloudinary":
                    g.timestamp_return_cloudinary = now_return
                elif origen == "supabase":
                    g.timestamp_return_supabase = now_return
                return result
            except Exception as e:
                now_return = datetime.datetime.now(datetime.timezone.utc)
                if origen == "firebase":
                    g.timestamp_return_firebase = now_return
                elif origen == "cloudinary":
                    g.timestamp_return_cloudinary = now_return
                elif origen == "supabase":
                    g.timestamp_return_supabase = now_return
                raise
        return wrapper
    return decorator


def before_request_log():
    """Hook para guardar el tiempo de llegada de la request."""
    g.request_id = str(uuid.uuid4())
    g.timestamp_arrival = datetime.datetime.now(datetime.timezone.utc)
    

def after_request_log(response):
    """Hook para guardar el tiempo de respuesta y crear el log."""
    
    """Hook para guardar el tiempo de respuesta y crear el log."""
    timestamp_response_sent = datetime.datetime.now(datetime.timezone.utc)

    # calcular diferencia en milisegundos
    response_time_ms = None
    if g.get("timestamp_arrival"):
        diff = timestamp_response_sent - g.get("timestamp_arrival")
        response_time_ms = int(diff.total_seconds() * 1000)  # milisegundos
        
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
        response_time_ms=response_time_ms
    )
    db.session.add(log)
    db.session.commit()
    return response