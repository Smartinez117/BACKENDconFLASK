import requests
from flask import Blueprint, request, jsonify

overpass_bp = Blueprint("overpass", __name__)

@overpass_bp.route('/api/refugios', methods=['POST'])
def obtener_refugios():
    """
    Recibe un query de Overpass desde el frontend, consulta la API y devuelve los resultados.
    """
    query = request.json.get('query')
    overpass_url = 'https://overpass-api.de/api/interpreter'

    try:
        response = requests.post(
            overpass_url,
            data={'data': query},
            headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        )
        response.raise_for_status()
        data = response.json()
        return jsonify(data), 200
    except Exception as error:
        return jsonify({'error': 'Error al consultar Overpass API', 'detalle': str(error)}), 500