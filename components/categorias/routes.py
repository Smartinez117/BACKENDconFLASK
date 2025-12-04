from flask import Blueprint, request, jsonify, g
from core.models import Categoria
categorias_bp = Blueprint("categorias", __name__)

from flask import Blueprint, jsonify
from core.models import Categoria, db
from functools import lru_cache # Importar esto

categorias_bp = Blueprint("categorias", __name__)

# Función auxiliar con caché
# maxsize=1 significa que guarda solo 1 resultado (la lista completa)
@lru_cache(maxsize=1) 
def get_cached_categories():
    return db.session.query(Categoria.id, Categoria.nombre, Categoria.descripcion)\
            .order_by(Categoria.id)\
            .all()

@categorias_bp.route('/api/categorias', methods=['GET'])
def get_categorias():
    try:
        # Llamamos a la función cacheada
        # La PRIMERA vez irá a la DB.
        # Las siguientes veces retornará lo que tiene en memoria RAM instantáneamente.
        cats = get_cached_categories()

        return jsonify([
            {
                "id": c.id, 
                "nombre": c.nombre, 
                "descripcion": c.descripcion
            } for c in cats
        ]), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500