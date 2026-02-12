import builtins
# Mantenemos esto por compatibilidad de algunas libs viejas de Python 2/3
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
# 1. IMPORTANTE: Importar ProxyFix para Google Cloud Run/Render
from werkzeug.middleware.proxy_fix import ProxyFix

from flask_apscheduler import APScheduler
from sqlalchemy import text

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
from core.models import db, Usuario, Notificacion 
from datetime import datetime, timezone

from dotenv import load_dotenv
import firebase_admin

load_dotenv()

app = Flask(__name__)

# 2. IMPORTANTE: Configurar ProxyFix
# Esto le dice a Flask que confíe en los headers HTTPS de Cloud Run
app.wsgi_app = ProxyFix(
    app.wsgi_app, 
    x_for=1, 
    x_proto=1, 
    x_host=1, 
    x_prefix=1
)


app.config['SCHEDULER_API_ENABLED'] = True
scheduler = APScheduler()


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

# Configuración Firebase
service_account_info = {
    "type": os.environ.get("FIREBASE_TYPE"),
    "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
    "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": str(os.environ.get("FIREBASE_PRIVATE_KEY")).replace('\\n', '\n'),
    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
    "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
    "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.environ.get("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL"),
    "universe_domain": os.environ.get("FIREBASE_UNIVERSE_DOMAIN")
}

# Inicializar Firebase
cred = credentials.Certificate(service_account_info)
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
frontend_url = os.getenv("FRONTEND_URL", "*")  

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
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

# 3. CAMBIO CRÍTICO: Quitamos el url_prefix aquí
# Porque ya lo pusiste manualmente en routes.py (/api/etiquetas)
app.register_blueprint(etiquetas_bp) 

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
        headers["Access-Control-Allow-Origin"] = "*"
        headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return resp

def tarea_archivar_publicaciones():
    with app.app_context():
        try:
            print(f"[{datetime.now()}] Iniciando proceso de archivado...")
            sql_query = text("""
                UPDATE publicaciones 
                SET estado = 1 
                WHERE estado = 0 
                AND COALESCE(fecha_modificacion, fecha_creacion) < NOW() - INTERVAL '6 months'
                RETURNING id, id_usuario, titulo
            """)
            
            result = db.session.execute(sql_query)
            archivos_procesados = result.fetchall()
            if archivos_procesados:
                print(f"Se encontraron {len(archivos_procesados)} publicaciones para archivar.")
                
                for pub in archivos_procesados:
                    p_id = pub.id
                    p_usuario = pub.id_usuario
                    p_titulo = pub.titulo

                    nueva_noti = Notificacion(
                        id_usuario=p_usuario,
                        titulo='Publicación Archivada',
                        descripcion=f'Tu publicación "{p_titulo}" ha sido archivada automáticamente por inactividad (6 meses). Puedes desarchivarla desde tu perfil.',
                        tipo='sistema',
                        fecha_creacion=datetime.now(timezone.utc),
                        leido=False,
                        id_publicacion=p_id,
                        id_referencia=None
                    )
                    db.session.add(nueva_noti)

                db.session.commit()
                print(f"ÉXITO: {len(archivos_procesados)} publicaciones archivadas y usuarios notificados.")
            
            else:
                # Si no hay nada que archivar, hacemos commit igual para cerrar la transacción limpia
                db.session.commit()
                print("Sin cambios: No hay publicaciones antiguas pendientes.")
                
        except Exception as e:
            print(f"ERROR CRÍTICO en tarea programada: {e}")
            db.session.rollback() # Deshace todo si algo falla

            
if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(
        id='archivar_job', 
        func=tarea_archivar_publicaciones, 
        trigger='cron', 
        hour=3, 
        minute=0
    )
    
    app.run(host='0.0.0.0', port=5000, debug=True)