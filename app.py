import firebase_admin
import psycopg2
from firebase_admin import credentials, auth as firebase_auth
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from functools import wraps
from datetime import datetime

app = Flask(__name__)

# Inicializar Firebase
cred = credentials.Certificate("firebase/firebase-credentials.json")
firebase_admin.initialize_app(cred)

# Configuración de la base de datos con SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:redeMaster12312341234554377@redema-1.czgus8igm8d1.us-east-2.rds.amazonaws.com:5432/postgres' #Recordar escribir postgres:contraseña@localhost>5432/Redema ,donde la contraseñe es la que determinaron al descargar PGadmin
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
def get_connection():
    return psycopg2.connect(
        host="redema-1.czgus8igm8d1.us-east-2.rds.amazonaws.com",
        dbname="postgres",
        user="postgres",
        password="redeMaster12312341234554377",
        port = 5432
    )

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    id_token = data.get("token")

    try:
        # Decodificar token
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_uid = decoded_token['uid']
        email = decoded_token['email']
        nombre = decoded_token.get('name', '')
        foto_perfil = decoded_token.get('picture', '')

        # Conectarse a PostgreSQL
        conn = get_connection()
        cur = conn.cursor()

        # Verificar si el usuario ya existe
        cur.execute("SELECT * FROM usuario WHERE firebase_uid = %s", (firebase_uid,))
        usuario = cur.fetchone()

        if not usuario:
            # Insertar nuevo usuario
            cur.execute("""
                INSERT INTO usuario (nombre, email, foto_de_perfil, firebase_uid, fecha_registro)
                VALUES (%s, %s, %s, %s, %s)
            """, (nombre, email, foto_perfil, firebase_uid, datetime.utcnow()))

            conn.commit()

        cur.close()
        conn.close()

        return jsonify({"message": "Usuario autenticado correctamente"}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Token inválido o error interno"}), 401


CORS(app)


# Modelo de ejemplo
class Persona(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    edad = db.Column(db.Integer, nullable=False)

# Crear las tablas si no existen
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Base de datos conectada y tabla 'persona' lista."

@app.route('/create', methods=['POST'])
def create_record():
    data = request.json
    nueva_persona = Persona(nombre=data['nombre'], edad=data['edad'])
    db.session.add(nueva_persona)
    db.session.commit()
    return jsonify({'message': 'Persona creada correctamente.'}), 201

@app.route('/read', methods=['GET'])
def read_records():
    personas = Persona.query.all()
    resultado = [{'id': p.id, 'nombre': p.nombre, 'edad': p.edad} for p in personas]
    return jsonify(resultado), 200

@app.route('/read/<int:record_id>', methods=['GET'])
def read_record(record_id):
    persona = Persona.query.get_or_404(record_id)
    return jsonify({'id': persona.id, 'nombre': persona.nombre, 'edad': persona.edad}), 200

@app.route('/update/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    persona = Persona.query.get_or_404(record_id)
    data = request.json
    persona.nombre = data.get('nombre', persona.nombre)
    persona.edad = data.get('edad', persona.edad)
    db.session.commit()
    return jsonify({'message': 'Persona actualizada exitosamente.'}), 200

@app.route('/delete/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    persona = Persona.query.get_or_404(record_id)
    db.session.delete(persona)
    db.session.commit()
    return jsonify({'message': 'Persona eliminada exitosamente.'}), 200

if __name__ == '__main__':
    app.run(debug=True)
