import requests
from flask import Blueprint, request, jsonify

overpass_bp = Blueprint("overpass", __name__)

# OJO: Revisa si en tu app.py registraste este blueprint con 'url_prefix=/api'
# Si ya tiene prefijo, la ruta aquí debería ser solo '/refugios'.
# Si NO tiene prefijo, déjala como '/api/refugios'.
@overpass_bp.route('/api/refugios', methods=['POST'])
def obtener_refugios():
    """
    Recibe un query de Overpass desde el frontend, consulta la API y devuelve los resultados.
    """
    query = request.json.get('query')
    overpass_url = 'https://overpass-api.de/api/interpreter'

    try:
        # CAMBIO: Quitamos los headers manuales, requests lo hace solo
        response = requests.post(
            overpass_url,
            data={'data': query}
        )
        
        # Si Overpass devuelve error (ej: 400 Bad Request o 429 Too Many Requests)
        if response.status_code != 200:
            return jsonify({'error': 'Overpass API error', 'detalle': response.text}), response.status_code

        data = response.json()
        return jsonify(data), 200

    except Exception as error:
        return jsonify({'error': 'Error al consultar Overpass API', 'detalle': str(error)}), 500