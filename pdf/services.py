from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import qrcode
from core.models import Publicacion, Usuario
from datetime import datetime
from reportlab.lib.utils import ImageReader 

def generar_pdf_publicacion(publicacion_id):
    publicacion = Publicacion.query.get(publicacion_id)
    if not publicacion:
        return {"error": "Publicación no encontrada"}, 404

    usuario = Usuario.query.get(publicacion.id_usuario)

    # Crear QR
    qr_url = f"https://redema.vercel.app/publicacion/{publicacion_id}"
    qr_img = qrcode.make(qr_url)
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    # Crear PDF
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4

    # Texto principal
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, "Redema - Reporte de Publicación")

    c.setFont("Helvetica", 12)
    c.drawString(100, height - 100, f"Título: {publicacion.titulo}")
    c.drawString(100, height - 120, f"Categoría: {publicacion.categoria}")
    c.drawString(100, height - 140, f"Descripción:")
    c.setFont("Helvetica", 10)
    c.drawString(100, height - 160, f"{publicacion.descripcion[:100]}...")  # Solo un preview

    if usuario:
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 200, f"Publicado por: {usuario.nombre} - {usuario.email}")

    c.drawString(100, height - 220, f"Fecha: {publicacion.fecha_creacion.strftime('%Y-%m-%d') if publicacion.fecha_creacion else '-'}")

    # Agregar QR al PDF
    qr_image = ImageReader(qr_buffer)  #Adaptar BytesIO para ReportLab
    c.drawImage(qr_image, width - 200, height - 250, width=100, height=100)
   

    # Finalizar PDF
    c.showPage()
    c.save()
    pdf_buffer.seek(0)

    return pdf_buffer  # Devuelve el archivo listo para enviar
