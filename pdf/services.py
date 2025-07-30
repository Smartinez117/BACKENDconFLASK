from core.models import db, Publicacion, Imagen, Usuario
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import requests
import qrcode
from datetime import datetime
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image as PilImage
import os


def generar_pdf_publicacion(id_publicacion):
    publicacion = Publicacion.query.get(id_publicacion)
    if not publicacion:
        raise Exception("Publicación no encontrada")

    usuario = Usuario.query.get(publicacion.id_usuario)
    imagen = Imagen.query.filter_by(id_publicacion=id_publicacion).first()

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40

    # Estilos
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle(
        name="Normal",
        fontSize=12,
        leading=16,
        spaceAfter=12
    )
    style_title = styles['Title']

    # Título
    titulo = f"{publicacion.categoria.upper()}: {publicacion.titulo or ''}"
    p_titulo = Paragraph(titulo, style_title)
    w, h = p_titulo.wrap(width - 100, 50)
    p_titulo.drawOn(c, 50, y - h)
    y -= (h + 20)

    # Imagen principal
    if imagen:
        try:
            response = requests.get(imagen.url)
            if response.status_code == 200:
                img_data = BytesIO(response.content)
                pil_img = PilImage.open(img_data)
                img_width, img_height = pil_img.size

                max_display_height = 300
                display_width = width * 0.6
                display_height = display_width * img_height / img_width

                # Si se pasa del alto máximo, escalamos nuevamente
                if display_height > max_display_height:
                    display_height = max_display_height
                    display_width = display_height * img_width / img_height

                x_img = (width - display_width) / 2
                c.drawImage(ImageReader(pil_img), x_img, y - display_height, width=display_width, height=display_height)
                y -= (display_height + 20)
        except Exception as e:
            print("Error cargando imagen:", e)

    # Descripción
    descripcion = Paragraph(f"<b>Descripción:</b> {publicacion.descripcion or 'No disponible'}", style_normal)
    w, h = descripcion.wrap(width - 100, height)
    descripcion.drawOn(c, 50, y - h)
    y -= (h + 10)

    # Teléfono
    telefono = f"{usuario.telefono_pais or ''} {usuario.telefono_numero_local or ''}".strip() or "No disponible"
    parrafo_tel = Paragraph(f"<b>Contacto:</b> {telefono}", style_normal)
    w, h = parrafo_tel.wrap(width - 100, height)
    parrafo_tel.drawOn(c, 50, y - h)
    y -= (h + 10)

    # Ubicación
    if publicacion.coordenadas:
        lat, lon = publicacion.coordenadas
        direccion = coordenadas_a_direccion(lat, lon)
    else:
        direccion = "No disponible"

    parrafo_ubi = Paragraph(f"<b>Ubicación:</b> {direccion}", style_normal)
    w, h = parrafo_ubi.wrap(width - 100, height)
    parrafo_ubi.drawOn(c, 50, y - h)
    y -= (h + 10)

    # Fecha
    fecha = publicacion.fecha_creacion.strftime("%d/%m/%Y") if publicacion.fecha_creacion else "Desconocida"
    parrafo_fecha = Paragraph(f"<b>Fecha:</b> {fecha}", style_normal)
    w, h = parrafo_fecha.wrap(width - 100, height)
    parrafo_fecha.drawOn(c, 50, y - h)
    y -= (h + 20)

    # Código QR (abajo derecha)
    url = f"https://tusitio.com/publicacion/{id_publicacion}"
    qr = qrcode.make(url)
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_img = PilImage.open(qr_buffer)
    qr_size = 230  # tamaño más grande del QR
    c.drawImage(ImageReader(qr_img), width - qr_size - 10, 20, width=qr_size, height=qr_size)

    # Logo (abajo izquierda)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Sube a BACKENDconFLASK
    logo_path = os.path.join(base_dir, "Logo.jpg")  # Asegúrate que esté aquí

    
    if os.path.exists(logo_path):
        try:
            logo_reader = ImageReader(logo_path)
            c.drawImage(logo_reader, 30, 30, width=80, height=80, preserveAspectRatio=True, mask='auto')
            print("✅ Logo dibujado correctamente.")
        except Exception as e:
            print("❌ Error dibujando el logo:", e)
    else:
        print(f"❌ Logo NO encontrado en: {logo_path}")



    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def coordenadas_a_direccion(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        'format': 'json',
        'lat': lat,
        'lon': lon,
        'zoom': 16,
        'addressdetails': 1
    }
    headers = {
        'User-Agent': 'RedemaBot/1.0 (tucorreo@example.com)'
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        address = data.get('address', {})
        partes = [
            address.get('road'),
            address.get('suburb'),
            address.get('city') or address.get('town') or address.get('village'),
        ]
        return ', '.join([p for p in partes if p]) or "Ubicación no disponible"
    return "Ubicación no disponible"
