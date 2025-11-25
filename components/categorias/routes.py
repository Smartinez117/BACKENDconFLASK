from flask import Blueprint, request, jsonify, g
from core.models import Categoria
categorias_bp = Blueprint("categorias", __name__)

@categorias_bp.route('/api/categorias', methods=['GET'])
def get_categorias():
    try:
        cats = Categoria.query.all()
        # Retornamos lista de objetos {id, nombre, descripcion}
        return jsonify([
            {
                "id": c.id, 
                "nombre": c.nombre, 
                "descripcion": c.descripcion
            } for c in cats
        ]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500