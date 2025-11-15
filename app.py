import builtins
if not hasattr(builtins, "unicode"):
    builtins.unicode = str

import os
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

from dotenv import load_dotenv
import firebase_admin
#
from util import socketio
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


service_account_info = {
    "type": os.environ.get("FIREBASE_TYPE"),
    "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
    "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("FIREBASE_PRIVATE_KEY"),
    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
    "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
    "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.environ.get("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL"),
    "universe_domain": os.environ.get("FIREBASE_UNIVERSE_DOMAIN")
}

cred = credentials.Certificate(service_account_info)

# Inicializar Firebase
cred = credentials.Certificate("firebase/firebase-credentials.json")
firebase_admin.initialize_app(cred)

# Configuración de la base de datos con SQLAlchemy
# Configuración de SQLAlchemy con Supabase (Session Pooler)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)
frontend_url = os.getenv("FRONTEND_URL", "*")  # * como fallback
CORS(
    app,
    resources={r"/*": {"origins": [frontend_url]}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
)


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
app.register_blueprint(roles_bp)
app.register_blueprint(overpass_bp)
# MAIN
# Inicializas socketio con la app
socketio.init_app(app)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
