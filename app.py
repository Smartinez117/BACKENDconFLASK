import firebase_admin
import psycopg2
from firebase_admin import credentials, auth as firebase_auth
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from functools import wraps
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)

# Inicializar Firebase
cred = credentials.Certificate("firebase/firebase-credentials.json")
firebase_admin.initialize_app(cred)

# Configuración de la base de datos con SQLAlchemy
# Configuración de SQLAlchemy con Supabase (Session Pooler)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.rloagvhioijwvqgknuex:redeMaster12312341234554377@aws-0-us-east-2.pooler.supabase.com:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    id_token = data.get("token")

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        firebase_uid = decoded_token['uid']
        email = decoded_token.get('email')
        nombre = decoded_token.get('name', '')
        foto_perfil = decoded_token.get('picture', '')

        # Verificar si el usuario ya existe en la base de datos
        usuario = Usuario.query.filter_by(firebase_uid=firebase_uid).first()

        if not usuario:
            # Crear nuevo usuario con campos opcionales en NULL
            nuevo_usuario = Usuario(
                firebase_uid=firebase_uid,
                nombre=nombre,
                email=email,
                foto_perfil_url=foto_perfil,
                fecha_registro=datetime.utcnow(),
                # Los siguientes campos quedan en NULL automáticamente:
                # telefono_pais, telefono_numero, descripcion
            )
            db.session.add(nuevo_usuario)
            db.session.commit()

        return jsonify({"message": "Usuario autenticado correctamente"}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Token inválido o error interno"}), 401

CORS(app)


#MODELOS:
class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(28), unique=True, nullable=False)
    nombre = db.Column(db.Text)
    email = db.Column(db.Text)
    foto_perfil_url = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime)
    num_publicaciones = db.Column(db.Integer, default=0)
    num_publicaciones_dia = db.Column(db.Integer, default=0)
    telefono_pais = db.Column(db.Text)
    telefono_numero = db.Column(db.Text)
    descripcion = db.Column(db.Text)

    publicaciones = db.relationship('Publicacion', backref='usuario', lazy=True)
    ubicaciones = db.relationship('Ubicacion', backref='usuario', lazy=True)

class Ubicacion(db.Model):
    __tablename__ = 'ubicaciones'

    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nombre = db.Column(db.Text)
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)
    codigo_postal = db.Column(db.Integer)
    provincia = db.Column(db.Text)
    ciudad = db.Column(db.Text)
    calle = db.Column(db.Text)
    altura = db.Column(db.Integer)

    publicaciones = db.relationship('Publicacion', backref='ubicacion', lazy=True)

class Publicacion(db.Model):
    __tablename__ = 'publicaciones'

    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_ubicacion = db.Column(db.Integer, db.ForeignKey('ubicaciones.id'))
    grupo = db.Column(db.Text)
    categoria = db.Column(db.Integer)
    tipo = db.Column(db.Integer)
    fecha_creacion = db.Column(db.DateTime)
    fecha_modificacion = db.Column(db.DateTime)
    id_anterior = db.Column(db.Integer, db.ForeignKey('publicaciones.id'))
    id_siguiente = db.Column(db.Integer, db.ForeignKey('publicaciones.id'))
    descripcion = db.Column(db.Text)
    foto_url_1 = db.Column(db.Text)
    foto_url_2 = db.Column(db.Text)



# MAIN


if __name__ == '__main__':
    app.run(debug=True)
