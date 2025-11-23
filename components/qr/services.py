from io import BytesIO
import base64
import qrcode
import os
from urllib.parse import urljoin
from flask import has_app_context, current_app


def _get_frontend_url():
    """Obtiene la URL base del frontend desde `current_app.config` (si hay contexto) o desde la env var `FRONTEND_URL`.

    Devuelve una cadena sin slash final. Si no está definida, retorna el valor por defecto
    `http://localhost:3000`.
    """
    frontend_url = None
    try:
        if has_app_context():
            frontend_url = current_app.config.get('FRONTEND_URL')
    except Exception:
        frontend_url = None

    if not frontend_url:
        frontend_url = os.getenv('FRONTEND_URL')

    if not frontend_url:
        frontend_url = 'http://localhost:3000'

    return frontend_url.rstrip('/')


def generar_qr(id_publicacion):
    """Genera un código QR que apunta a la URL de una publicación específica.

    Usa la variable de entorno `FRONTEND_URL` o `current_app.config['FRONTEND_URL']` si existe.
    """
    base = _get_frontend_url()
    # Construir la URL de forma segura
    url = urljoin(base + '/', f'publicacion/{id_publicacion}')

    # Crear QR
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Guardar en memoria
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Devolver como base64 (útil si se quiere mostrar directamente en el frontend)
    qr_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return {
        "url_codificada": url,
        "imagen_base64": qr_base64
    }
