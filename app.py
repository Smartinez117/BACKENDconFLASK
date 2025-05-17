from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

# 📦 Conexión a la base de datos
def get_db_connection():
    conn = psycopg2.connect(
        dbname='presentacion1',  # aqui va el nombre de la base de datso creada en postgrest
        user='postgres',
        password='basededatos',
        host='localhost',
        port='5432'
    )
    return conn

#creacion de la base de datos en caso de que no exista
def create_table_if_not_exists():
    conn = get_db_connection()
    cur = conn.cursor()
    # despues lo arreglamos con los campos que se necesiten para el proyecto
    cur.execute("""
        CREATE TABLE IF NOT EXISTS carreras (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(50) UNIQUE NOT NULL
        )
    """)
    
    for carrera in ['mecanica', 'quimica', 'sistemas', 'electrica']:
        cur.execute("INSERT INTO carreras (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING;", (carrera,))
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tablaprueba1 (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            edad INTEGER NOT NULL,
            carrera_id INTEGER REFERENCES carreras(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

create_table_if_not_exists()



# 🎯 Rutas de la API (vacías, listas para implementar)

@app.route('/create', methods=['POST'])
def create_record():
    # Aquí iría la lógica para crear un registro
    return jsonify({'message': 'Función crear registro (a implementar).'}), 200

@app.route('/read', methods=['GET'])
def read_records():
    # Aquí iría la lógica para leer todos los registros
    return jsonify({'message': 'Función leer registros (a implementar).'}), 200

@app.route('/read/<int:record_id>', methods=['GET'])
def read_record(record_id):
    # Aquí iría la lógica para leer un registro específico
    return jsonify({'message': f'Función leer registro {record_id} (a implementar).'}), 200

@app.route('/update/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    # Aquí iría la lógica para actualizar un registro
    return jsonify({'message': f'Función actualizar registro {record_id} (a implementar).'}), 200

@app.route('/delete/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    # Aquí iría la lógica para eliminar un registro
    return jsonify({'message': f'Función eliminar registro {record_id} (a implementar).'}), 200

@app.route('/test_transactions', methods=['POST'])
def test_transactions():
    # Aquí iría la lógica para probar transacciones
    return jsonify({'message': 'Función test de transacciones (a implementar).'}), 200

if __name__ == '__main__':
    app.run(debug=True)
