from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pethomecare2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
# ==================== MODELOS ====================

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(60), nullable=False)
    apellidos = db.Column(db.String(60), nullable=False)
    documento = db.Column(db.String(20), unique=True, nullable=False)
    telefono = db.Column(db.String(15), nullable=False)
    direccion = db.Column(db.String(150), nullable=False)

class Mascota(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    especie = db.Column(db.String(30), nullable=False)
    raza = db.Column(db.String(50))
    edad_aprox = db.Column(db.Integer)
    observaciones = db.Column(db.Text)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    cliente = db.relationship('Cliente', backref=db.backref('mascotas', lazy=True))

class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False)
    frecuencia = db.Column(db.String(20), nullable=False)
    precio_ref = db.Column(db.Float, nullable=False)
    vigente = db.Column(db.Boolean, default=True)

class Servicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)

class Suscripcion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False)
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascota.id'), nullable=False)
    fecha_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(15), default='Activa')
    cliente = db.relationship('Cliente')
    plan = db.relationship('Plan')
    mascota = db.relationship('Mascota')

class Cita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascota.id'), nullable=False)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicio.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    franja_horaria = db.Column(db.String(15), nullable=False)
    direccion = db.Column(db.String(150), nullable=False)
    estado = db.Column(db.String(15), default='Solicitada')
    mascota = db.relationship('Mascota')
    servicio = db.relationship('Servicio')

class Tratamiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cita_id = db.Column(db.Integer, db.ForeignKey('cita.id'), unique=True, nullable=False)
    procedimiento = db.Column(db.String(200), nullable=False)
    observaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    cita = db.relationship('Cita')
    # ==================== RUTAS ====================

@app.route('/')
def index():
    return render_template('index.html')

# --- FLUJO 1: REGISTRAR DUEÑO ---
@app.route('/registrar_dueno', methods=['GET', 'POST'])
def registrar_dueno():
    if request.method == 'POST':
        nuevo_cliente = Cliente(
            nombres=request.form['nombres'],
            apellidos=request.form['apellidos'],
            documento=request.form['documento'],
            telefono=request.form['telefono'],
            direccion=request.form['direccion']
        )
        db.session.add(nuevo_cliente)
        db.session.commit()
        flash('Dueño registrado exitosamente. Ahora inscribe a tu mascota.', 'success')
        return redirect(url_for('inscribir_mascota', cliente_id=nuevo_cliente.id))
    return render_template('registro_dueno.html')

# --- FLUJO 1 (cont): INSCRIBIR MASCOTA ---
@app.route('/inscribir_mascota/<int:cliente_id>', methods=['GET', 'POST'])
def inscribir_mascota(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if request.method == 'POST':
        nueva_mascota = Mascota(
            nombre=request.form['nombre'],
            especie=request.form['especie'],
            raza=request.form['raza'],
            edad_aprox=request.form['edad_aprox'],
            observaciones=request.form['observaciones'],
            cliente_id=cliente_id
        )
        db.session.add(nueva_mascota)
        db.session.commit()
        flash('Mascota inscrita exitosamente. Ahora puedes contratar un plan.', 'success')
        return redirect(url_for('contratar_plan', cliente_id=cliente_id))
    return render_template('inscribir_mascota.html', cliente=cliente)

# --- FLUJO 2: CONTRATAR PLAN ---
@app.route('/contratar_plan/<int:cliente_id>', methods=['GET', 'POST'])
def contratar_plan(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    planes = Plan.query.filter_by(vigente=True).all()
    mascotas = Mascota.query.filter_by(cliente_id=cliente_id).all()
    if request.method == 'POST':
        nueva_suscripcion = Suscripcion(
            cliente_id=cliente_id,
            plan_id=request.form['plan_id'],
            mascota_id=request.form['mascota_id']
        )
        db.session.add(nueva_suscripcion)
        db.session.commit()
        flash('Plan contratado exitosamente. Ahora programa una cita.', 'success')
        return redirect(url_for('programar_cita', cliente_id=cliente_id))
    return render_template('contratar_plan.html', cliente=cliente, planes=planes, mascotas=mascotas)

# --- FLUJO 3: PROGRAMAR CITA ---
@app.route('/programar_cita/<int:cliente_id>', methods=['GET', 'POST'])
def programar_cita(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    servicios = Servicio.query.all()
    mascotas = Mascota.query.filter_by(cliente_id=cliente_id).all()
    if request.method == 'POST':
        fecha_cita = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
        nueva_cita = Cita(
            mascota_id=request.form['mascota_id'],
            servicio_id=request.form['servicio_id'],
            fecha=fecha_cita,
            franja_horaria=request.form['franja_horaria'],
            direccion=cliente.direccion,
            estado='Confirmada'
        )
        db.session.add(nueva_cita)
        db.session.commit()
        flash('Cita programada y confirmada exitosamente.', 'success')
        return redirect(url_for('index'))
    return render_template('programar_cita.html', cliente=cliente, servicios=servicios, mascotas=mascotas)

# --- FLUJO 4: REGISTRAR TRATAMIENTO ---
@app.route('/registrar_tratamiento/<int:cita_id>', methods=['GET', 'POST'])
def registrar_tratamiento(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    if request.method == 'POST':
        nuevo_tratamiento = Tratamiento(
            cita_id=cita_id,
            procedimiento=request.form['procedimiento'],
            observaciones=request.form['observaciones']
        )
        cita.estado = 'Atendida'
        db.session.add(nuevo_tratamiento)
        db.session.commit()
        flash('Tratamiento registrado. La cita ha sido marcada como Atendida.', 'success')
        return redirect(url_for('admin'))
    return render_template('registrar_tratamiento.html', cita=cita)

# --- PANEL ADMIN (evidencia) ---
@app.route('/admin')
def admin():
    clientes = Cliente.query.all()
    mascotas = Mascota.query.all()
    citas = Cita.query.all()
    tratamientos = Tratamiento.query.all()
    return render_template('admin.html', clientes=clientes, mascotas=mascotas, citas=citas, tratamientos=tratamientos)
    # ==================== INICIALIZACIÓN ====================

def inicializar_datos():
    """Crea tablas y datos de prueba si la base de datos está vacía."""
    db.create_all()
    if not Plan.query.first():
        db.session.add_all([
            Plan(nombre='Plan Salud Esencial', frecuencia='Mensual', precio_ref=120000),
            Plan(nombre='Plan Estética Premium', frecuencia='Mensual', precio_ref=180000),
            Plan(nombre='Plan Integral Anual', frecuencia='Anual', precio_ref=1500000),
        ])
        db.session.add_all([
            Servicio(nombre='Consulta Veterinaria', tipo='Salud'),
            Servicio(nombre='Vacunación', tipo='Salud'),
            Servicio(nombre='Baño y Corte', tipo='Estética'),
            Servicio(nombre='Relajación Canina', tipo='Estética'),
        ])
        db.session.commit()
        print('✅ Datos de prueba cargados.')

if __name__ == '__main__':
    with app.app_context():
        inicializar_datos()
    app.run(debug=True, host='0.0.0.0', port=5000)
    