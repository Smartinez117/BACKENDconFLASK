import builtins
# Mantenemos esto por compatibilidad de algunas libs viejas de Python 2/3
if not hasattr(builtins, "unicode"):
    builtins.unicode = str

import os
import json
import psycopg2
from firebase_admin import credentials, auth as firebase_auth
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from functools import wraps
from datetime import datetime
from flask_migrate import Migrate

# Imports de modelos y rutas
from core.models import db, Usuario
from auth.routes import auth_bp
from components.publicaciones.routes import publicaciones_bp
from components.usuarios.routes import usuarios_bp
from components.comentarios.routes import comentarios_bp
from components.imagenes.routes import imagenes_bp
from components.notificaciones.routes import notificaciones_bp
from components.reportes.routes import reportes_bp
from components.qr.routes import qr_bp
from components.pdf.routes import pdf_bp
from components.ubicacion.routes import ubicacion_bp
from components.etiquetas.routes import etiquetas_bp
from components.roles.routes import roles_bp
from components.refugios.routes import overpass_bp
from components.funcionesAdmin.routes import admin_bp
from components.categorias.routes import categorias_bp
from components.contactos.routes import contactos_bp

from dotenv import load_dotenv
import firebase_admin

load_dotenv()

app = Flask(__name__)

def cerrar_sesion():
    """
    Cierra la sesión de base de datos de forma segura.
    """
    try:
        db.session.remove()  # limpia y cierra la sesión actual
    except Exception as error:
        print(f"Error al cerrar la sesión: {error}")

@app.teardown_appcontext
def shutdown_session(exception=None):
    """Cierra la sesión de base de datos al finalizar el contexto de la app."""
    cerrar_sesion()

# Inicializar Firebase
# cred = credentials.Certificate("firebase/firebase-credentials.json")
cred = credentials.Certificate(json.loads(os.environ["FIREBASE_CREDENTIALS"]))
firebase_admin.initialize_app(cred)

# Configuración de la base de datos con SQLAlchemy (Session Pooler optimizado)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_size": 5,         
    "max_overflow": 10,     
    "pool_timeout": 30,     
    "pool_recycle": 1800,   
    "pool_pre_ping": True   
}

db.init_app(app)
migrate = Migrate(app, db)
frontend_url = os.getenv("FRONTEND_URL")  # * como fallback
CORS(
    app,
    resources={r"/*": {"origins": frontend_url}},
    supports_credentials=False,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
)

# Cloudinary
app.config['CLOUDINARY_CLOUD_NAME'] = os.getenv("CLOUDINARY_CLOUD_NAME")
app.config['CLOUDINARY_API_KEY'] = os.getenv("CLOUDINARY_API_KEY")
app.config['CLOUDINARY_API_SECRET'] = os.getenv("CLOUDINARY_API_SECRET")
app.config['CLOUDINARY_UPLOAD_PRESET'] = os.getenv("CLOUDINARY_UPLOAD_PRESET")

# Registrar Blueprints
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
app.register_blueprint(roles_bp)
app.register_blueprint(overpass_bp)
app.register_blueprint(admin_bp, url_prefix="/api")
app.register_blueprint(categorias_bp)
app.register_blueprint(contactos_bp)

@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        resp = app.make_default_options_response()
        headers = resp.headers

        headers["Access-Control-Allow-Origin"] = frontend_url
        headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return resp


@app.route('/')
def health_check():
    return "Ok"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
