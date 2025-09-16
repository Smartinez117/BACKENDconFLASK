from flask import Blueprint, send_file
from components.pdf.services import generar_pdf_publicacion

pdf_bp = Blueprint("pdf", __name__)

@pdf_bp.route("/pdf/<int:id_publicacion>", methods=["GET"])
def descargar_pdf(id_publicacion):
    '''Genera y descarga el PDF de una publicación específica.'''
    pdf = generar_pdf_publicacion(id_publicacion)
    if isinstance(pdf, tuple):  # Si es un error
        return pdf
    return send_file(pdf, mimetype='application/pdf', as_attachment=True,
                     download_name=f"publicacion_{id_publicacion}.pdf")
