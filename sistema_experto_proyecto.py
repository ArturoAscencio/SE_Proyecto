# -*- coding: utf-8 -*-
"""
Created on Sat Jun 15 22:17:47 2024

@author: 52331
"""
from flask import Flask, request, render_template_string, redirect, url_for
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from experta import *

# Configuración de la Base de Datos
Base = declarative_base()

class Paciente(Base):
    __tablename__ = 'pacientes'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    edad = Column(Integer)
    genero = Column(String)
    historial_medico = Column(String, nullable=True)

class Sintoma(Base):
    __tablename__ = 'sintomas'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    descripcion = Column(String)

class Diagnostico(Base):
    __tablename__ = 'diagnosticos'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    descripcion = Column(String)
    tratamiento_recomendado = Column(String)

class Regla(Base):
    __tablename__ = 'reglas'
    id = Column(Integer, primary_key=True)
    regla = Column(String)
    resultado = Column(String)

engine = create_engine('sqlite:///sistema_experto.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Poblar la base de datos si está vacía
session = Session()
if session.query(Sintoma).count() == 0:
    sintomas = [
        Sintoma(nombre='dolor_pecho', descripcion='Dolor en el pecho'),
        Sintoma(nombre='dificultad_respirar', descripcion='Dificultad para respirar'),
        Sintoma(nombre='falta_aire', descripcion='Falta de aire'),
        Sintoma(nombre='dolor_muscular', descripcion='Dolor muscular'),
        Sintoma(nombre='mareo', descripcion='Mareo'),
        Sintoma(nombre='fatiga', descripcion='Fatiga'),
        Sintoma(nombre='palpitaciones', descripcion='Palpitaciones'),
        Sintoma(nombre='hinchazon_tobillos', descripcion='Hinchazón de tobillos'),
    ]
    session.add_all(sintomas)

if session.query(Diagnostico).count() == 0:
    diagnosticos = [
        Diagnostico(nombre='angina', descripcion='Angina', tratamiento_recomendado='Tratamiento para la angina'),
        Diagnostico(nombre='infarto', descripcion='Infarto', tratamiento_recomendado='Tratamiento para el infarto'),
        Diagnostico(nombre='insuficiencia_cardiaca', descripcion='Insuficiencia cardíaca', tratamiento_recomendado='Tratamiento para insuficiencia cardíaca'),
        Diagnostico(nombre='arritmia', descripcion='Arritmia', tratamiento_recomendado='Tratamiento para la arritmia'),
    ]
    session.add_all(diagnosticos)

if session.query(Regla).count() == 0:
    reglas = [
        Regla(regla='dolor_pecho', resultado='angina'),
        Regla(regla='dificultad_respirar', resultado='infarto'),
        Regla(regla='falta_aire', resultado='insuficiencia_cardiaca'),
        Regla(regla='palpitaciones', resultado='arritmia'),
    ]
    session.add_all(reglas)

session.commit()
session.close()

# Motor de Inferencia con experta
class DiagnosticoEnfermedad(KnowledgeEngine):

    @DefFacts()
    def _initial_action(self):
        yield Fact(action='find_disease')    
 
    @Rule(Fact(action='find_disease'),
          Fact(sintoma='Molestias_fisicas'), 
          Fact(sintoma='Sudoracion'),
          Fact(sintoma='Dolor_muscular'),
          Fact(sintoma='dolor_pecho'))
    def enfermedad1(self):
        self.declare(Fact(diagnostico='angina'))

    @Rule(Fact(action='find_disease'), 
          Fact(sintoma='Molestias_fisicas'), 
          Fact(sintoma='Sudoracion'),
          Fact(sintoma='Dolor_muscular'),
          Fact(sintoma='Nauseas'),
          Fact(sintoma='Aturdimiento_mareos'),
          Fact(sintoma='Falta_aire'),
          Fact(sintoma='Fatiga'),
          Fact(sintoma='dolor_pecho'))
    def enfermedad2(self):
        self.declare(Fact(diagnostico='infarto'))

    @Rule(Fact(action='find_disease'), 
          Fact(sintoma='Dolor_muscular'), 
          Fact(sintoma='Fatiga'),
          Fact(sintoma='Falta_aire'),
          Fact(sintoma='Retencion_liquidos'))
    def enfermedad3(self):
        self.declare(Fact(diagnostico='insuficiencia_cardiaca'))

    @Rule(Fact(action='find_disease'), 
          Fact(sintoma='dificultad_respirar'), 
          Fact(sintoma='Pitidos_oidos'),
          Fact(sintoma='Vision_borrosa'),
          Fact(sintoma='Nauseas'),
          Fact(sintoma='Cambio_ritmo_cardiaco'),
          Fact(sintoma='dolor_pecho'))
    def enfermedad4(self):
        self.declare(Fact(diagnostico='hipertension arterial'))
        
    @Rule(Fact(sintoma='Cambio_ritmo_cardiaco'))
    def enfermedad5(self):
        self.declare(Fact(diagnostico='Transtorno de ritmo cardiaco'))
          
    @Rule(Fact(sintoma='Fatiga'),
          Fact(sintoma='Dolor_muscular'))
    def enfermedad6(self):
        self.declare(Fact(diagnostico='Exceso de colesterol'))

    @Rule(Fact(diagnostico=MATCH.d))
    def mostrar_diagnostico(self, d):
        self.diagnostico = d
        print(f"Diagnóstico: {d}")

    def obtener_diagnostico(self, sintomas):
        self.reset()
        for sintoma in sintomas:
            self.declare(Fact(sintoma=sintoma))
        self.run()
        return getattr(self, 'diagnostico', 'No se pudo determinar el diagnóstico')


# Aplicación Flask
app = Flask(__name__)

@app.route('/')
def index():
    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sistema Experto</title>
    </head>
    <body>
        <h1>Sistema Experto de Enfermedades Cardiovasculares</h1>
        <form action="/preguntas" method="post">
            <label for="nombre">Nombre:</label><br>
            <input type="text" id="nombre" name="nombre"><br>
            <label for="edad">Edad:</label><br>
            <input type="number" id="edad" name="edad"><br>
            <label for="genero">Género:</label><br>
            <select id="genero" name="genero">
                <option value="masculino">Masculino</option>
                <option value="femenino">Femenino</option>
            </select><br><br>
            <input type="submit" value="Iniciar Encuesta">
        </form>
    </body>
    </html>
    '''
    return render_template_string(template)

@app.route('/preguntas', methods=['POST'])
def preguntas():
    nombre = request.form['nombre']
    edad = int(request.form['edad'])
    genero = request.form['genero']

    # Guardar datos del paciente en la base de datos
    session = Session()
    nuevo_paciente = Paciente(nombre=nombre, edad=edad, genero=genero)
    session.add(nuevo_paciente)
    session.commit()
    paciente_id = nuevo_paciente.id
    session.close()

    return redirect(url_for('pregunta', idx=0, paciente_id=paciente_id))

@app.route('/pregunta/<int:idx>/<int:paciente_id>')
def pregunta(idx, paciente_id):
    session = Session()
    sintomas = session.query(Sintoma).all()
    session.close()

    if idx < len(sintomas):
        sintoma = sintomas[idx]
        return renderizar_pregunta(sintoma, idx, paciente_id)
    else:
        return redirect(url_for('diagnostico', paciente_id=paciente_id))

def renderizar_pregunta(sintoma, idx, paciente_id):
    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sistema Experto</title>
    </head>
    <body>
        <h1>Sistema Experto de Enfermedades Cardiovasculares</h1>
        <form action="{{ url_for('respuesta', idx=idx, paciente_id=paciente_id) }}" method="post">
            <p>{{ sintoma.descripcion }}?</p>
            <input type="radio" id="si" name="respuesta" value="si">
            <label for="si">Sí</label><br>
            <input type="radio" id="no" name="respuesta" value="no">
            <label for="no">No</label><br><br>
            <input type="submit" value="Siguiente">
        </form>
    </body>
    </html>
    '''
    return render_template_string(template, sintoma=sintoma, idx=idx, paciente_id=paciente_id)

@app.route('/respuesta/<int:idx>/<int:paciente_id>', methods=['POST'])
def respuesta(idx, paciente_id):
    respuesta = request.form['respuesta']

    session = Session()
    sintomas = session.query(Sintoma).all()
    paciente = session.query(Paciente).filter_by(id=paciente_id).first()

    if not paciente.historial_medico:
        paciente.historial_medico = ''

    if respuesta == 'si':
        paciente.historial_medico += sintomas[idx].nombre + ';'

    session.commit()
    session.close()

    idx += 1
    if idx < len(sintomas):
        return redirect(url_for('pregunta', idx=idx, paciente_id=paciente_id))
    else:
        return redirect(url_for('diagnostico', paciente_id=paciente_id))

@app.route('/diagnostico/<int:paciente_id>')
def diagnostico(paciente_id):
    session = Session()
    paciente = session.query(Paciente).filter_by(id=paciente_id).first()
    sintomas_seleccionados = paciente.historial_medico.split(';')[:-1]

    engine = DiagnosticoEnfermedad()
    diagnostico = engine.obtener_diagnostico(sintomas_seleccionados)

    paciente.historial_medico += f'Diagnóstico: {diagnostico}'
    session.commit()
    session.close()

    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sistema Experto</title>
    </head>
    <body>
        <h1>Sistema Experto de Enfermedades Cardiovasculares</h1>
        <p>Gracias, {{ nombre }}. Basado en tus respuestas, el diagnóstico preliminar es: <strong>{{ diagnostico }}</strong>.</p>
    </body>
    </html>
    '''
    return render_template_string(template, nombre=paciente.nombre, diagnostico=diagnostico)

if __name__ == '__main__':
    app.run(debug=True)
