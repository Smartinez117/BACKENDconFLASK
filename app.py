from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuración de la base de datos con SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:hola123@localhost:5432/Redema'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
    return jsonify({'message': 'Persona creada.'}), 201

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
