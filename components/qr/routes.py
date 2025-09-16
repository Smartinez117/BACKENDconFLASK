from flask import Blueprint, jsonify
from components.qr.services import generar_qr

qr_bp = Blueprint("qr", __name__)

@qr_bp.route('/qr/<int:id_publicacion>', methods=["GET"])
def obtener_qr(id_publicacion):
    '''Genera y devuelve un código QR para la publicación con el ID dado.'''
    resultado = generar_qr(id_publicacion)
    return jsonify(resultado), 200
