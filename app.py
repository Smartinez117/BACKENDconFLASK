import firebase_admin
import psycopg2
from firebase_admin import credentials, auth as firebase_auth
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from functools import wraps
from datetime import datetime
from flask_migrate import Migrate
from core.models import db, Usuario
from auth.routes import auth_bp
from publicaciones.routes import publicaciones_bp
from usuarios.routes import usuarios_bp
from comentarios.routes import comentarios_bp
from imagenes.routes import imagenes_bp
from notificaciones.routes import notificaciones_bp
from reportes.routes import reportes_bp
from qr.routes import qr_bp
from pdf.routes import pdf_bp
from ubicacion.routes import ubicacion_bp
from etiquetas.routes import etiquetas_bp
from dotenv import load_dotenv
import os

load_dotenv()




app = Flask(__name__)

# Inicializar Firebase
cred = credentials.Certificate("firebase/firebase-credentials.json")
firebase_admin.initialize_app(cred)

# Configuración de la base de datos con SQLAlchemy
# Configuración de SQLAlchemy con Supabase (Session Pooler)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)
CORS(app)


# Configuración a cloudinary
# Cloudinary
app.config['CLOUDINARY_CLOUD_NAME'] = os.getenv("CLOUDINARY_CLOUD_NAME")
app.config['CLOUDINARY_API_KEY'] = os.getenv("CLOUDINARY_API_KEY")
app.config['CLOUDINARY_API_SECRET'] = os.getenv("CLOUDINARY_API_SECRET")
app.config['CLOUDINARY_UPLOAD_PRESET'] = os.getenv("CLOUDINARY_UPLOAD_PRESET")

app.register_blueprint(auth_bp)
app.register_blueprint(publicaciones_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(comentarios_bp)
app.register_blueprint(imagenes_bp)
app.register_blueprint(notificaciones_bp)
app.register_blueprint(reportes_bp)
app.register_blueprint(qr_bp)
app.register_blueprint(pdf_bp)
app.register_blueprint(ubicacion_bp)
app.register_blueprint(etiquetas_bp, url_prefix='/api/etiquetas')
# MAIN


if __name__ == '__main__':
    app.run(debug=True)
