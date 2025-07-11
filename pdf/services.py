from core.models import db, Publicacion, Imagen, Usuario
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import requests
import qrcode
from datetime import datetime
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image as PilImage
from reportlab.lib.styles import ParagraphStyle

def generar_pdf_publicacion(id_publicacion):
    publicacion = Publicacion.query.get(id_publicacion)
    if not publicacion:
        raise Exception("Publicación no encontrada")

    usuario = Usuario.query.get(publicacion.id_usuario)
    imagen = Imagen.query.filter_by(id_publicacion=id_publicacion).first()

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50


    
    
    styles = getSampleStyleSheet()
    styleN = ParagraphStyle(
        name='Normal',
        fontSize=20,  #  Aumenta este valor
        leading=16    #  Espaciado entre líneas
    )
    styleT = styles['Title']

    # Título de la categoría
    titulo = f"{publicacion.categoria.upper()}: {publicacion.titulo or ''}"
    p_titulo = Paragraph(titulo, styleT)
    p_titulo.wrapOn(c, width - 100, 50)
    p_titulo.drawOn(c, 50, y)
    y -= 70

    # Imagen principal centrada
    if imagen:
        try:
            response = requests.get(imagen.url)
            if response.status_code == 200:
                img_data = BytesIO(response.content)
                pil_img = PilImage.open(img_data)
                img_width, img_height = pil_img.size

                display_width = width / 2
                display_height = display_width * img_height / img_width
                x_pos = (width - display_width) / 2

                c.drawImage(ImageReader(pil_img), x_pos, y - display_height, width=display_width, height=display_height)
                y -= (display_height + 30)
        except Exception as e:
            print("Error cargando imagen:", e)

    # Descripción
    descripcion = Paragraph(f"<b>Descripción:</b> {publicacion.descripcion or 'No disponible'}", styleN)
    descripcion.wrapOn(c, width - 100, 100)
    descripcion.drawOn(c, 50, y)
    y -= 100

    # Teléfono
    telefono = f"{usuario.telefono_pais or ''} {usuario.telefono_numero_local or ''}".strip() or "No disponible"
    parrafo_tel = Paragraph(f"<b>Contacto:</b> {telefono}", styleN)
    parrafo_tel.wrapOn(c, width - 100, 20)
    parrafo_tel.drawOn(c, 50, y)
    y -= 25

    # Ubicación resumida
    if publicacion.coordenadas:
        lat, lon = publicacion.coordenadas
        direccion = coordenadas_a_direccion(lat, lon)
    else:
        direccion = "No disponible"
    parrafo_ubi = Paragraph(f"<b>Ubicación:</b> {direccion}", styleN)
    parrafo_ubi.wrapOn(c, width - 100, 40)
    parrafo_ubi.drawOn(c, 50, y)
    y -= 30

    # Fecha
    fecha = publicacion.fecha_creacion.strftime("%d/%m/%Y") if publicacion.fecha_creacion else "Desconocida"
    parrafo_fecha = Paragraph(f"<b>Fecha:</b> {fecha}", styleN)
    parrafo_fecha.wrapOn(c, width - 100, 20)
    parrafo_fecha.drawOn(c, 50, y)
    y -= 40

    # QR con enlace a la publicación
    url = f"https://tusitio.com/publicacion/{id_publicacion}"
    qr = qrcode.make(url)
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_img = PilImage.open(qr_buffer)
    c.drawImage(ImageReader(qr_img), width - 150, 40, width=100, height=100)

    # Finalizar
    c.showPage()
    c.save()
    buffer.seek(0)

    return buffer



def coordenadas_a_direccion(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse"
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
            address.get('road'),                # calle
            address.get('suburb'),              # barrio
            address.get('city') or address.get('town') or address.get('village'),  # ciudad/pueblo
        ]
        
        # Filtrar nulos y unir con coma
        direccion_resumida = ', '.join([p for p in partes if p])
        return direccion_resumida or "Ubicación no disponible"
    
    return "Ubicación no disponible"
