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

app = Flask(__name__)

# Inicializar Firebase
cred = credentials.Certificate("firebase/firebase-credentials.json")
firebase_admin.initialize_app(cred)

# Configuración de la base de datos con SQLAlchemy
# Configuración de SQLAlchemy con Supabase (Session Pooler)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres.rloagvhioijwvqgknuex:redeMaster12312341234554377@aws-0-us-east-2.pooler.supabase.com:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)
CORS(app)



app.register_blueprint(auth_bp)





# MAIN


if __name__ == '__main__':
    app.run(debug=True)
