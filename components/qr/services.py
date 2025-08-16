import qrcode
from io import BytesIO
import base64

def generar_qr(id_publicacion):
    # URL que se codificará en el QR
    url = f"http://localhost:5173/publicacion/{id_publicacion}"

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
