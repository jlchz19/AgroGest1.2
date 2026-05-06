

import os
import uuid
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response, send_from_directory, send_file
from werkzeug.utils import secure_filename
from sqlalchemy import text, or_
from sqlalchemy.exc import OperationalError as SAOperationalError
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import os
import socket
import requests
from config import Config
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env si existe
load_dotenv()
# Importaciones para PDF eliminadas - funcionalidad de reportes removida

from io import BytesIO
import threading
import time
import secrets
import string

# Importaciones para códigos QR
try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    print("[WARNING] QRCode no está instalado. La funcionalidad de códigos QR no estará disponible.")

# Importaciones para el scheduler
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    import atexit
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("[WARNING] APScheduler no está instalado. Las alertas automáticas no funcionarán.")

# Importaciones opcionales para email
try:
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import smtplib
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("[WARNING] Módulos de email no disponibles.")

def enviar_notificacion_email(usuario, alerta):
    """Envía notificación por email cuando se crea una alerta usando Gmail SMTP"""
    if not EMAIL_AVAILABLE:
        print("[WARNING] No se puede enviar email - módulos no disponibles")
        return False

    try:
        email_usuario = os.getenv('EMAIL_USER', 'joseluischirinos380@gmail.com')
        email_password = os.getenv('EMAIL_PASSWORD', 'aphtvabqvticwzwv')  # clave de aplicación de Gmail

        if not email_password:
            print("[ERROR] EMAIL_PASSWORD no está configurado. No se puede enviar el email de alerta.")
            return False

        # Construir cuerpo HTML con estilo moderno
        asunto = f"Nueva Alerta AgroGest: {alerta.titulo}"
        cuerpo_html = f"""
        <html>
        <head>
            <meta charset="utf-8" />
        </head>
        <body style="margin:0;padding:0;background-color:#f4f4f4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f4f4f4;padding:24px 0;">
                <tr>
                    <td align="center">
                        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:560px;background-color:#ffffff;border-radius:12px;box-shadow:0 4px 18px rgba(15,23,42,0.12);overflow:hidden;">
                            <tr>
                                <td style="background:linear-gradient(135deg,#16a34a,#22c55e);padding:16px 24px;color:#ecfdf5;">
                                    <div style="font-size:14px;letter-spacing:.08em;text-transform:uppercase;opacity:.9;">AgroGest · Alerta</div>
                                    <div style="margin-top:4px;font-size:22px;font-weight:600;display:flex;align-items:center;gap:8px;">
                                        <span>&#128276;</span>
                                        <span>Nueva alerta programada</span>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding:24px 24px 8px 24px;color:#0f172a;font-size:15px;line-height:1.6;">
                                    <p style="margin:0 0 12px 0;">Hola <strong>{usuario.nombre} {usuario.apellido}</strong>,</p>
                                    <p style="margin:0 0 16px 0;">Se ha creado una nueva alerta en tu sistema de gestión agropecuaria <strong>AgroGest</strong>:</p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding:0 24px 16px 24px;">
                                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:separate;border-spacing:0 8px;">
                                        <tr>
                                            <td style="background-color:#f9fafb;border-radius:8px;padding:12px 14px;">
                                                <div style="font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;margin-bottom:4px;">T\u00edtulo</div>
                                                <div style="font-size:15px;color:#111827;font-weight:600;">{alerta.titulo}</div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="background-color:#f9fafb;border-radius:8px;padding:12px 14px;">
                                                <div style="font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;margin-bottom:4px;">Descripci\u00f3n</div>
                                                <div style="font-size:14px;color:#111827;">{alerta.descripcion}</div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="background-color:#ecfdf3;border-radius:8px;padding:12px 14px;display:flex;justify-content:space-between;align-items:center;">
                                                <div>
                                                    <div style="font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#15803d;margin-bottom:4px;">Fecha programada</div>
                                                    <div style="font-size:14px;color:#064e3b;font-weight:600;">{alerta.fecha_programada.strftime('%d/%m/%Y %H:%M')}</div>
                                                </div>
                                                <div style="font-size:24px;">&#128197;</div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="background-color:#eef2ff;border-radius:8px;padding:12px 14px;display:flex;justify-content:space-between;align-items:center;">
                                                <div>
                                                    <div style="font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#4f46e5;margin-bottom:4px;">Tipo de alerta</div>
                                                    <div style="font-size:14px;color:#111827;font-weight:500;">{alerta.tipo_alerta}</div>
                                                </div>
                                                <div style="font-size:22px;">&#9881;&#65039;</div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding:8px 24px 24px 24px;color:#6b7280;font-size:12px;line-height:1.6;border-top:1px solid #e5e7eb;">
                                    <p style="margin:12px 0 4px 0;">Este es un mensaje autom\u00e1tico generado por <strong>AgroGest</strong>. No respondas a este correo.</p>
                                    <p style="margin:0;">Si no reconoces esta alerta o tienes alguna duda, contacta con el administrador del sistema.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        mensaje = MIMEMultipart('alternative')
        mensaje['From'] = email_usuario
        mensaje['To'] = usuario.email
        mensaje['Subject'] = asunto
        mensaje.attach(MIMEText(cuerpo_html, 'html'))

        # Enviar usando Gmail SMTP
        try:
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.login(email_usuario, email_password)
                server.sendmail(email_usuario, [usuario.email], mensaje.as_string())
            print(f"[INFO] Email de alerta enviado a {usuario.email} vía Gmail.")
            return True
        except Exception as e:
            print(f"[ERROR] Fallo al enviar email de alerta vía Gmail: {e}")
            return False

    except Exception as e:
        print(f"[ERROR] No se pudo preparar el email de alerta: {e}")
        return False


# ---- Utilitarios de roles ----
from functools import wraps

def role_required(roles):
    """Decorator to require a role (or list of roles) on current_user."""
    if isinstance(roles, str):
        allowed = {roles}
    else:
        allowed = set(roles)

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user or not getattr(current_user, 'is_authenticated', False):
                flash('Necesitas iniciar sesión', 'warning')
                return redirect(url_for('login'))
            if getattr(current_user, 'rol', None) not in allowed:
                flash('Permiso denegado', 'danger')
                return redirect(url_for('empleados'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

def generar_token_seguro(longitud=32):
    """Genera un token aleatorio seguro para recuperación de contraseña"""
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

def enviar_email_recuperacion(usuario, token):
    """Envía email con enlace de recuperación de contraseña usando Gmail SMTP"""
    if not EMAIL_AVAILABLE:
        print("[WARNING] No se puede enviar email - módulos no disponibles")
        return False

    try:
        email_usuario = os.getenv('EMAIL_USER', 'joseluischirinos380@gmail.com')
        email_password = os.getenv('EMAIL_PASSWORD', 'aphtvabqvticwzwv')  # clave de aplicación de Gmail

        if not email_password:
            print("[ERROR] EMAIL_PASSWORD no está configurado. No se puede enviar el email de recuperación.")
            return False

        # En este flujo, 'token' es un código numérico de verificación
        codigo = token

        asunto = "Código de Recuperación - AgroGest"
        cuerpo_html = f"""
        <html>
        <head>
            <meta charset="utf-8" />
        </head>
        <body style="margin:0;padding:0;background-color:#f4f4f4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f4f4f4;padding:24px 0;">
                <tr>
                    <td align="center">
                        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:560px;background-color:#ffffff;border-radius:12px;box-shadow:0 4px 18px rgba(15,23,42,0.12);overflow:hidden;">
                            <tr>
                                <td style="background:linear-gradient(135deg,#16a34a,#22c55e);padding:16px 24px;color:#ecfdf5;">
                                    <div style="font-size:14px;letter-spacing:.08em;text-transform:uppercase;opacity:.9;">AgroGest · Recuperación</div>
                                    <div style="margin-top:4px;font-size:22px;font-weight:600;display:flex;align-items:center;gap:8px;">
                                        <span>&#128274;</span>
                                        <span>Código de recuperación</span>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding:24px 24px 8px 24px;color:#0f172a;font-size:15px;line-height:1.6;">
                                    <p style="margin:0 0 12px 0;">Hola <strong>{usuario.nombre} {usuario.apellido}</strong>,</p>
                                    <p style="margin:0 0 16px 0;">Recibimos una solicitud para restablecer la contraseña de tu cuenta en <strong>AgroGest</strong>.</p>
                                    <p style="margin:0 0 16px 0;">Utiliza el siguiente código para completar el proceso de recuperación. Introdúcelo en la pantalla de verificación de código.</p>
                                </td>
                            </tr>
                            <tr>
                                <td align="center" style="padding:4px 24px 20px 24px;">
                                    <div style="display:inline-block;padding:12px 28px;border-radius:999px;background:linear-gradient(135deg,#22c55e,#16a34a);color:#ecfdf5;font-size:24px;font-weight:700;letter-spacing:0.35em;">{codigo}</div>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding:0 24px 16px 24px;color:#4b5563;font-size:12px;line-height:1.7;">
                                    <p style="margin:0 0 10px 0;">Este código es válido por <strong>1 hora</strong> y solo puede usarse una vez.</p>
                                    <p style="margin:0 0 10px 0;">Si no solicitaste este cambio, puedes ignorar este mensaje. Tu contraseña actual seguirá siendo válida.</p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding:8px 24px 20px 24px;border-top:1px solid #e5e7eb;color:#9ca3af;font-size:11px;line-height:1.6;">
                                    <p style="margin:10px 0 4px 0;">Este correo ha sido enviado automáticamente por <strong>AgroGest</strong>; no respondas a este mensaje.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        mensaje = MIMEMultipart('alternative')
        mensaje['From'] = email_usuario
        mensaje['To'] = usuario.email
        mensaje['Subject'] = asunto
        mensaje.attach(MIMEText(cuerpo_html, 'html'))

        # Enviar usando Gmail SMTP
        try:
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.login(email_usuario, email_password)
                server.sendmail(email_usuario, [usuario.email], mensaje.as_string())
            print(f"[INFO] Email de recuperación enviado a {usuario.email} vía Gmail.")
            return True
        except Exception as e:
            print(f"[ERROR] Fallo al enviar email de recuperación vía Gmail: {e}")
            return False

    except Exception as e:
        print(f"[ERROR] No se pudo preparar el email de recuperación: {e}")
        return False

from sqlalchemy import func
from sqlalchemy.orm import aliased, load_only, defer
from sqlalchemy.sql.expression import extract
from werkzeug.utils import secure_filename
import pandas as pd
import config # Importar el archivo de configuración
from flask import make_response, send_file
import io
from functools import wraps
from types import SimpleNamespace

# Importación opcional de WeasyPrint
WEASYPRINT_AVAILABLE = False
HTML = None
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    WEASYPRINT_AVAILABLE = False

app = Flask(__name__)
# Cargar configuración desde el archivo config.py
app.config.from_object(config.DevelopmentConfig)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finca_ganadera.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Asegurar que el directorio de uploads existe
UPLOAD_FOLDER = os.path.join('static', 'animales')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Additional upload locations for empleados
UPLOAD_BASE = os.path.join(app.root_path, 'static', 'uploads')
UPLOAD_EMPLEADOS = os.path.join(UPLOAD_BASE, 'empleados')
UPLOAD_CEDULAS = os.path.join(UPLOAD_BASE, 'cedulas')
UPLOAD_MAQUINARIA = os.path.join(UPLOAD_BASE, 'maquinaria')
IMAGENES_UBICACIONES = os.path.join(app.root_path, 'static', 'imagenes_ubicaciones')

# Crear directorios necesarios si no existen
os.makedirs(UPLOAD_EMPLEADOS, exist_ok=True)
os.makedirs(UPLOAD_CEDULAS, exist_ok=True)
os.makedirs(UPLOAD_MAQUINARIA, exist_ok=True)
os.makedirs(IMAGENES_UBICACIONES, exist_ok=True)

# Folder for personal reference documents (pdf, doc, images)
UPLOAD_REFERENCIAS = os.path.join(UPLOAD_BASE, 'referencias')
os.makedirs(UPLOAD_REFERENCIAS, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return filename and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_empleado_columns():
    """Adds missing columns to empleado table if they don't exist (safe to call multiple times)."""
    try:
        needed = {
            'nacionalidad': 'TEXT',
            'condiciones_enfermedades': 'TEXT',
            'referencia_personal': 'TEXT',
            'referencia_file': 'TEXT',
            'alergico_medicamento': 'INTEGER',
            'alergias_medicamento': 'TEXT',
            'foto_empleado': 'TEXT',
            'foto_cedula': 'TEXT',
            'fecha_ingreso': 'DATE'
        }
        # Use SQLAlchemy 2.x style connection execution
        with db.engine.begin() as conn:
            res = conn.execute(text("PRAGMA table_info('empleado')")).fetchall()
            existing_cols = [r[1] for r in res]
            for col, sqltype in needed.items():
                if col not in existing_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE empleado ADD COLUMN {col} {sqltype}"))
                        print(f"[INFO] Added missing column '{col}' to empleado table.")
                    except Exception as e:
                        print(f"[WARNING] Could not add column {col}: {e}")
    except Exception as e:
        print(f"[WARNING] ensure_empleado_columns failed: {e}")

def ensure_potrero_columns():
    """Asegura que las columnas necesarias existan en la tabla potrero"""
    try:
        # Verificar si la columna imagen existe en la tabla potrero
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('potrero')]
        if 'imagen' not in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE potrero ADD COLUMN imagen VARCHAR(255)"))
                conn.commit()
                print("Columna 'imagen' agregada a la tabla potrero")
    except Exception as e:
        print(f"Error ensuring potrero columns: {e}")

def ensure_maquinaria_columns():
    """Asegura que las columnas necesarias existan en la tabla maquinaria"""
    try:
        # Verificar si la columna imagen existe en la tabla maquinaria
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('maquinaria')]
        if 'imagen' not in columns:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE maquinaria ADD COLUMN imagen VARCHAR(255)"))
                conn.commit()
                print("Columna 'imagen' agregada a la tabla maquinaria")
    except Exception as e:
        print(f"Error ensuring maquinaria columns: {e}")

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ruta estática para servir imágenes desde la carpeta 'imagen' en la raíz del proyecto
@app.route('/imagen/<path:filename>')
def imagen_static(filename):
    # Obtener la ruta absoluta a la carpeta 'imagen' en la raíz del proyecto
    imagen_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'imagen'))
    print(f"[DEBUG] Intentando servir imagen: {filename} desde: {imagen_dir}")
    return send_from_directory(imagen_dir, filename)

# Inicializar base de datos si no existe
def update_database():
    with app.app_context():
        # Check if column exists before adding it
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(ubicacion)"))
            columns = [row[1] for row in result]
            if 'imagen' not in columns:
                conn.execute(text('ALTER TABLE ubicacion ADD COLUMN imagen VARCHAR(255)'))
                conn.commit()
        db.session.commit()
        print("Database updated successfully!")

with app.app_context():
    try:
        db.create_all()
        # Add the imagen column to ubicacion table if it doesn't exist
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(ubicacion)"))
            columns = [row[1] for row in result]
            if 'imagen' not in columns:
                conn.execute(text('ALTER TABLE ubicacion ADD COLUMN imagen VARCHAR(255)'))
                conn.commit()
        db.session.commit()
        print("[INFO] Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"[ERROR] Error al inicializar la base de datos: {e}")

    # Ensure new columns in Empleado exist (useful when model changed without migrations)
    try:
        # Mapping of desired columns and SQL types
        needed = {
            'nacionalidad': 'TEXT',
            'condiciones_enfermedades': 'TEXT',
            'referencia_personal': 'TEXT',
            'referencia_file': 'TEXT',
            'alergico_medicamento': 'INTEGER',
            'alergias_medicamento': 'TEXT',
            'foto_empleado': 'TEXT',
            'foto_cedula': 'TEXT',
            'fecha_ingreso': 'DATE'
        }
        # Use SQLAlchemy 2.x style connection execution
        with db.engine.begin() as conn:
            res = conn.execute(text("PRAGMA table_info('empleado')")).fetchall()
            existing_cols = [r[1] for r in res]
            for col, sqltype in needed.items():
                if col not in existing_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE empleado ADD COLUMN {col} {sqltype}"))
                        print(f"[INFO] Se añadió columna '{col}' a la tabla empleado.")
                    except Exception as e:
                        print(f"[WARNING] No se pudo añadir columna {col}: {e}")
    except Exception as e:
        print(f"[WARNING] No fue posible comprobar/actualizar columnas de empleado: {e}")

    # Google OAuth column creation removed

    # Modelos de la base de datos
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    direccion = db.Column(db.String(200))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='activo')  # activo, inactivo
    rol = db.Column(db.String(20), default='usuario')  # admin, usuario

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

class Finca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    extension = db.Column(db.Float)  # en hectáreas
    tipo_produccion = db.Column(db.String(50))  # leche, carne, doble propósito, etc.
    propietario = db.Column(db.String(100))
    telefono = db.Column(db.String(30))
    email = db.Column(db.String(120))
    fecha_fundacion = db.Column(db.Date)
    descripcion = db.Column(db.Text)
    ubicacion = db.Column(db.String(200))  # municipio, departamento, país
    # Nuevos campos para el mapa
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)
    poligono_geojson = db.Column(db.Text)  # Para almacenar el polígono dibujado
    imagen_mapa = db.Column(db.String(255))  # Ruta a la imagen del mapa
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))  # Dueño de la finca
    animales = db.relationship('Animal', backref='finca', lazy=True)
    potreros = db.relationship('Potrero', backref='finca', lazy=True)
    empleados = db.relationship('Empleado', backref='finca', lazy=True)
    vacunas = db.relationship('Vacuna', backref='finca', lazy=True)
    producciones = db.relationship('Produccion', backref='finca', lazy=True)
    inventarios = db.relationship('Inventario', backref='finca', lazy=True)

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identificacion = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(100))  # Nuevo campo para nombre del animal
    tipo = db.Column(db.String(20), nullable=False)  # vaca, cochino, etc.
    raza = db.Column(db.String(50), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    peso = db.Column(db.Float, nullable=False)
    peso_nacimiento = db.Column(db.Float)  # Peso al nacer
    estado = db.Column(db.String(20), default='activo')  # activo, vendido, muerto
    potrero_id = db.Column(db.Integer, db.ForeignKey('potrero.id'))  # Potrero asignado (para bovinos principalmente)
    ubicacion_id = db.Column(db.Integer, db.ForeignKey('ubicacion.id'))  # Ubicación específica según tipo de animal
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    imagen = db.Column(db.String(200))  # Ruta de la imagen
    finca_id = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)
    padre_id = db.Column(db.Integer, db.ForeignKey('animal.id'))
    madre_id = db.Column(db.Integer, db.ForeignKey('animal.id'))
    sexo = db.Column(db.String(10))  # Macho o Hembra
    
    # Información adicional para registro completo
    color_señas = db.Column(db.String(200))  # Color y señas particulares
    ubicacion_actual = db.Column(db.String(100))  # Ubicación específica (corral, paridera, etc.)
    
    # Información genética y reproductiva (genérica para todos los animales)
    numero_crias_camada = db.Column(db.Integer)  # Número de crías por camada/parto
    peso_promedio_crias = db.Column(db.Float)  # Peso promedio de las crías
    produccion_diaria = db.Column(db.Float)  # Producción diaria (leche, huevos, etc.)
    unidad_produccion = db.Column(db.String(20))  # Unidad de producción (litros, huevos, kg)
    
    # Historial reproductivo (para hembras de cualquier especie)
    fecha_servicio = db.Column(db.Date)  # Fecha de servicio/inseminación/monta
    semental_utilizado = db.Column(db.String(100))  # ID del semental/macho utilizado
    fecha_estimada_parto = db.Column(db.Date)  # Fecha estimada de parto/nacimiento
    fecha_real_parto = db.Column(db.Date)  # Fecha real de parto/nacimiento
    crias_nacidas_vivas = db.Column(db.Integer)  # Crías nacidas vivas (lechones, terneros, corderos, etc.)
    crias_nacidas_muertas = db.Column(db.Integer)  # Crías nacidas muertas
    peso_promedio_crias_nacimiento = db.Column(db.Float)  # Peso promedio de crías al nacer
    numero_partos = db.Column(db.Integer, default=0)  # Número total de partos
    
    # Historial reproductivo (para machos reproductores de cualquier especie)
    fecha_inicio_semental = db.Column(db.Date)  # Fecha de inicio como reproductor
    numero_servicios_exitosos = db.Column(db.Integer, default=0)  # Servicios/montas exitosos
    promedio_crias_por_camada = db.Column(db.Float)  # Promedio de crías por camada de sus parejas
    
    # Información de venta/compra
    fecha_venta = db.Column(db.Date)
    comprador = db.Column(db.String(100))
    peso_venta = db.Column(db.Float)
    precio_venta = db.Column(db.Float)
    
    # Información de fallecimiento
    fecha_fallecimiento = db.Column(db.Date)
    causa_fallecimiento = db.Column(db.String(200))
    disposicion_final = db.Column(db.String(100))  # Incineración, entierro, etc.
    
    # Observaciones generales
    observaciones = db.Column(db.Text)
    
    # Relaciones
    historial_alimentacion = db.relationship('HistorialAlimentacion', backref='animal', lazy=True, cascade='all, delete-orphan')
    historial_salud = db.relationship('HistorialSalud', backref='animal', lazy=True, cascade='all, delete-orphan')
    notas = db.relationship('NotaAnimal', backref='animal', lazy=True, cascade='all, delete-orphan')
    historial_potreros = db.relationship('HistorialPotrero', backref='animal', lazy=True, cascade='all, delete-orphan')
    potrero = db.relationship('Potrero', backref='animales', lazy=True)

# Nuevos modelos para el registro completo

class HistorialAlimentacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    tipo_alimento = db.Column(db.String(100), nullable=False)  # Pre-inicio, Inicio, Crecimiento, Engorde
    marca = db.Column(db.String(100))
    composicion = db.Column(db.Text)
    cantidad_diaria = db.Column(db.Float)
    unidad = db.Column(db.String(20))  # kg, litros, etc.
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date)
    observaciones = db.Column(db.Text)

class HistorialSalud(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    tipo_evento = db.Column(db.String(50), nullable=False)  # enfermedad, lesión, desparasitación, vacunación, parto, etc.
    descripcion = db.Column(db.Text, nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date)
    tratamiento = db.Column(db.Text)
    dias_tratamiento = db.Column(db.Integer)
    resultado = db.Column(db.String(50))  # Total, Parcial, Sin recuperación
    observaciones = db.Column(db.Text)
    veterinario = db.Column(db.String(100))
    costo_tratamiento = db.Column(db.Float)
    estado = db.Column(db.String(20), default='activo')  # activo, finalizado, en_tratamiento
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

# Modelo para imágenes de eventos de salud
class ImagenEventoSalud(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evento_salud_id = db.Column(db.Integer, db.ForeignKey('evento_salud.id', ondelete='CASCADE'), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    ruta_archivo = db.Column(db.String(500), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_registro = db.Column(db.String(100))
    
    # Relación con evento de salud
    evento = db.relationship('EventoSalud', backref='imagenes', lazy=True)

# Nuevo modelo para eventos de salud integral
class EventoSalud(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    tipo_evento = db.Column(db.String(50), nullable=False)  # enfermedad, parto, vacunación, desparasitación, lesión, etc.
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_evento = db.Column(db.Date, nullable=False)
    hora_evento = db.Column(db.Time, default=datetime.now().time())
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, en_progreso, completado, cancelado
    
    # Campos para tratamiento médico
    diagnostico = db.Column(db.Text)
    tratamiento = db.Column(db.Text)
    medicamento = db.Column(db.String(200))
    dosis = db.Column(db.String(100))
    via_administracion = db.Column(db.String(50))  # oral, intramuscular, intravenosa, etc.
    duracion_tratamiento = db.Column(db.Integer)  # días
    proxima_dosis = db.Column(db.Date)
    
    # Campos específicos para partos
    tipo_parto = db.Column(db.String(50))  # normal, distocia, cesárea
    numero_crias = db.Column(db.Integer)
    crias_vivas = db.Column(db.Integer)
    crias_muertas = db.Column(db.Integer)
    peso_crias = db.Column(db.Float)
    complicaciones = db.Column(db.Text)
    
    # Campos para vacunación
    tipo_vacuna = db.Column(db.String(100))
    lote_vacuna = db.Column(db.String(100))
    fecha_proxima_dosis = db.Column(db.Date)
    
    # Responsable y costos
    veterinario = db.Column(db.String(100))
    responsable = db.Column(db.String(100))
    
    # Seguimiento
    resultado = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    fecha_recuperacion = db.Column(db.Date)
    
    # Auditoría
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_registro = db.Column(db.String(100))
    
    # Relaciones
    animal = db.relationship('Animal', lazy=True)


# --- Nuevos modelos: módulo reproductivo avanzado ---
class ServicioReproductivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    tipo_servicio = db.Column(db.String(30), nullable=False)  # monta natural, inseminacion
    semental_id = db.Column(db.Integer, db.ForeignKey('animal.id'))  # opcional
    semental_nombre = db.Column(db.String(100))
    responsable = db.Column(db.String(100))  # empleado/veterinario
    observaciones = db.Column(db.Text)

class DiagnosticoPrenez(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    resultado = db.Column(db.String(20), nullable=False)  # preñada, vacía, dudoso
    metodo = db.Column(db.String(50))  # palpación, eco, laboratorio
    semanas_gestacion = db.Column(db.Integer)
    observaciones = db.Column(db.Text)

class Parto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    crias_vivas = db.Column(db.Integer)
    crias_muertas = db.Column(db.Integer)
    peso_promedio_crias = db.Column(db.Float)
    dificultades = db.Column(db.String(200))
    observaciones = db.Column(db.Text)

class Potrero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    area = db.Column(db.Float, nullable=False)  # en hectáreas
    capacidad = db.Column(db.Integer, nullable=False)  # número máximo de animales
    tipo_pasto = db.Column(db.String(100))
    estado = db.Column(db.String(20), default='disponible')  # disponible, ocupado, mantenimiento
    funcion = db.Column(db.String(100), nullable=False)  # función del potrero
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    imagen = db.Column(db.String(255))  # ruta de la imagen del potrero
    finca_id = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)

class Ubicacion(db.Model):
    """Modelo para ubicaciones específicas según tipo de animal"""
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo_ubicacion = db.Column(db.String(50), nullable=False)  # corral, gallinero, cochiquera, establo, etc.
    tipo_animal = db.Column(db.String(50), nullable=False)  # Bovino, Porcino, Aviar, Equino, etc.
    capacidad = db.Column(db.Integer, nullable=False)  # número de animales
    area = db.Column(db.Float)  # en metros cuadrados
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(20), default='disponible')  # disponible, ocupado, mantenimiento
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    imagen = db.Column(db.String(255))  # ruta de la imagen de la ubicación
    finca_id = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)
    
    # Relación con animales
    animales_ubicacion = db.relationship('Animal', backref='ubicacion_asignada', lazy=True, foreign_keys='Animal.ubicacion_id')

class Vacuna(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    tipo_vacuna = db.Column(db.String(100), nullable=False)
    fecha_aplicacion = db.Column(db.Date, nullable=False)
    fecha_proxima = db.Column(db.Date, nullable=False)
    observaciones = db.Column(db.Text)
    aplicada_por = db.Column(db.String(100), nullable=False)
    finca_id = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)
    numero_lote = db.Column(db.String(50))
    fecha_vencimiento = db.Column(db.Date)
    # Agregar relación para acceder a animal desde vacuna
    animal = db.relationship('Animal', backref='vacunas', lazy=True)
    # Nuevo: relación con empleado (veterinario)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'))
    veterinario = db.relationship('Empleado', backref='vacunas_aplicadas', lazy=True)
    # Nuevos campos para datos del veterinario
    veterinario_nombre = db.Column(db.String(100))
    veterinario_apellido = db.Column(db.String(100))
    veterinario_cargo = db.Column(db.String(100))
    # Campo para estado de la vacuna (pendiente, aplicada, vencida)
    estado = db.Column(db.String(20), nullable=False, default='pendiente')
    veterinario_telefono = db.Column(db.String(30))

class Empleado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    cargo = db.Column(db.String(50), nullable=True)  # dejar abierta la posibilidad del cargo
    nacionalidad = db.Column(db.String(50))
    condiciones_enfermedades = db.Column(db.Text)
    referencia_personal = db.Column(db.String(200))
    referencia_file = db.Column(db.String(255))
    alergico_medicamento = db.Column(db.Boolean, default=False)
    alergias_medicamento = db.Column(db.Text)
    foto_empleado = db.Column(db.String(255))
    foto_cedula = db.Column(db.String(255))
    fecha_ingreso = db.Column(db.Date)
    fecha_contratacion = db.Column(db.Date, nullable=False)
    salario = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='activo')  # activo, inactivo
    finca_id = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)




class Produccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    tipo_produccion = db.Column(db.String(50), nullable=False)  # leche, carne, etc.
    cantidad = db.Column(db.Float, nullable=False)
    unidad = db.Column(db.String(20), nullable=False)  # litros, kg, etc.
    fecha = db.Column(db.Date, nullable=False)
    calidad = db.Column(db.String(20), default='buena')  # buena, regular, mala
    finca_id = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)
    # Agregar relación para acceder a animal desde produccion
    animal = db.relationship('Animal', backref='producciones', lazy=True)



class Inventario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    unidad = db.Column(db.String(20), nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_vencimiento = db.Column(db.Date)
    categoria = db.Column(db.String(50), nullable=False)  # alimento, medicina, equipos, etc.
    tipo_animal = db.Column(db.String(20))  # vaca, cochino, etc.
    finca_id = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)

# Historial de movimientos de inventario
class MovimientoInventario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventario_id = db.Column(db.Integer, db.ForeignKey('inventario.id'), nullable=False)
    tipo_movimiento = db.Column(db.String(20), nullable=False)  # entrada, salida, ajuste
    cantidad = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.String(200))

class MovimientoInventarioAnimal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventario_id = db.Column(db.Integer, db.ForeignKey('inventario.id'), nullable=False)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.String(200))
    observaciones = db.Column(db.Text)
    inventario = db.relationship('Inventario', lazy=True)
    animal = db.relationship('Animal', lazy=True)

# --- Costos y Rentabilidad ---
class CentroCosto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    finca_id = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)

# --- Gestión de Cámaras ---
class Camara(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    estado = db.Column(db.String(20), default='activo')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    finca_id = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)
    posicion = db.Column(db.Integer)  # Para ordenar las cámaras

    def __repr__(self):
        return f'<Camara {self.nombre}>'

class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    finca_id = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)
    centro_costo_id = db.Column(db.Integer, db.ForeignKey('centro_costo.id'))
    categoria = db.Column(db.String(50), nullable=False)  # alimento, medicina, mano_obra, mantenimiento, otros
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.Text)
    potrero_id = db.Column(db.Integer, db.ForeignKey('potrero.id'))
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'))
    centro_costo = db.relationship('CentroCosto', lazy=True)

class Ingreso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    finca_id = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)
    concepto = db.Column(db.String(100), nullable=False)  # venta leche, venta animal, otros
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.Text)

# Notas o comentarios en animales
class NotaAnimal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    nota = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class HistorialPotrero(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    potrero_id = db.Column(db.Integer, db.ForeignKey('potrero.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.String(200))  # Motivo o comentario del cambio
    
    # Eliminar la siguiente línea para evitar conflicto de backref:
    # animal = db.relationship('Animal', backref='historial_potreros', lazy=True)
    potrero = db.relationship('Potrero', lazy=True)

# Modelo para tokens de recuperación de contraseña
class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_expiracion = db.Column(db.DateTime, nullable=False)
    usado = db.Column(db.Boolean, default=False)
    
    usuario = db.relationship('Usuario', backref='password_reset_tokens', lazy=True)

# Modelo para registrar eventos importantes de animales
class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    tipo_evento = db.Column(db.String(50), nullable=False)  # 'fallecido', 'vendido', 'transferido', etc.
    fecha_evento = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.Text)
    responsable = db.Column(db.String(100))  # persona que registró el evento
    comprador = db.Column(db.String(200))  # para eventos de venta
    precio_venta = db.Column(db.Float)  # para eventos de venta
    causa_muerte = db.Column(db.String(200))  # para eventos de fallecimiento
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    animal = db.relationship('Animal', backref='eventos', lazy=True)

    def __repr__(self):
        return f'<Evento {self.tipo_evento} - Animal {self.animal_id}>'

# Modelo para Maquinaria
class Maquinaria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    finca_id = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)  # Nombre de la máquina (ej: "Tractor John Deere 5075")
    tipo = db.Column(db.String(50), nullable=False)  # Tipo de maquinaria (tractor, cosechadora, pulverizadora, etc.)
    marca = db.Column(db.String(50))  # Marca (John Deere, Case IH, New Holland, etc.)
    modelo = db.Column(db.String(50))  # Modelo específico
    numero_serie = db.Column(db.String(100))  # Número de serie
    año_fabricacion = db.Column(db.Integer)  # Año de fabricación
    fecha_adquisicion = db.Column(db.Date)  # Fecha de compra/adquisición
    valor_compra = db.Column(db.Float)  # Valor de compra
    estado = db.Column(db.String(20), default='operativo')  # operativo, en_mantenimiento, fuera_servicio, vendido
    ubicacion_actual = db.Column(db.String(100))  # Ubicación actual en la finca
    horas_uso = db.Column(db.Float, default=0)  # Horas de uso (para tractores, etc.)
    ultimo_mantenimiento = db.Column(db.Date)  # Fecha del último mantenimiento
    proximo_mantenimiento = db.Column(db.Date)  # Próximo mantenimiento programado
    responsable = db.Column(db.String(100))  # Persona responsable de la máquina
    observaciones = db.Column(db.Text)  # Observaciones adicionales
    imagen = db.Column(db.String(255))  # Ruta a la imagen de la maquinaria
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    finca = db.relationship('Finca', backref='maquinarias', lazy=True)
    
    def __repr__(self):
        return f'<Maquinaria {self.nombre} - Finca {self.finca_id}>'

# Modelo para Mantenimiento de Maquinaria
class MantenimientoMaquinaria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    maquinaria_id = db.Column(db.Integer, db.ForeignKey('maquinaria.id'), nullable=False)
    tipo_mantenimiento = db.Column(db.String(50), nullable=False)  # preventivo, correctivo, emergencia
    descripcion = db.Column(db.Text, nullable=False)  # Descripción del mantenimiento realizado
    fecha_mantenimiento = db.Column(db.Date, nullable=False)
    costo = db.Column(db.Float)  # Costo del mantenimiento
    tecnico = db.Column(db.String(100))  # Nombre del técnico que realizó el mantenimiento
    piezas_cambiadas = db.Column(db.Text)  # Lista de piezas cambiadas
    proximo_mantenimiento = db.Column(db.Date)  # Próximo mantenimiento según este servicio
    responsable_registro = db.Column(db.String(100))  # Quién registró el mantenimiento
    observaciones = db.Column(db.Text)  # Observaciones adicionales
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    maquinaria = db.relationship('Maquinaria', backref='mantenimientos', lazy=True)
    
    def __repr__(self):
        return f'<Mantenimiento {self.tipo_mantenimiento} - Maquinaria {self.maquinaria_id}>'

# Usar el decorador de Flask-Login en lugar del personalizado
# El decorador personalizado se mantiene para compatibilidad pero no se usa
def login_required_custom(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_finca_alertas(finca_id):
    """Recopila alertas importantes para una finca específica."""
    alertas = []
    today = date.today()
    limite_proximidad = today + timedelta(days=15)

    # Alerta 1: Vacunas próximas a vencer
    vacunas_proximas = Vacuna.query.join(Animal).filter(
        Vacuna.finca_id == finca_id,
        Vacuna.fecha_proxima >= today,
        Vacuna.fecha_proxima <= limite_proximidad
    ).order_by(Vacuna.fecha_proxima).all()

    for vacuna in vacunas_proximas:
        animal = Animal.query.get(vacuna.animal_id)
        dias_faltantes = (vacuna.fecha_proxima - today).days
        alertas.append({
            'tipo': 'vacuna',
            'mensaje': f"Vacuna '{vacuna.tipo_vacuna}' para el animal '{animal.identificacion}' vence en {dias_faltantes} días.",
            'url': url_for('vacunas')
        })

    # Alerta 2: Inventario por caducar
    inventario_por_caducar = Inventario.query.filter(
        Inventario.finca_id == finca_id,
        Inventario.fecha_vencimiento.isnot(None),
        Inventario.fecha_vencimiento >= today,
        Inventario.fecha_vencimiento <= limite_proximidad
    ).order_by(Inventario.fecha_vencimiento).all()
    
    for item in inventario_por_caducar:
        dias_faltantes = (item.fecha_vencimiento - today).days
        alertas.append({
            'tipo': 'inventario_caduca',
            'mensaje': f"El producto '{item.producto}' caduca en {dias_faltantes} días.",
            'url': url_for('inventario')
        })

    # Alerta 3: Bajo inventario (ej. cantidad < 10)
    bajo_inventario = Inventario.query.filter(
        Inventario.finca_id == finca_id,
        Inventario.cantidad < 10
    ).all()

    for item in bajo_inventario:
         alertas.append({
            'tipo': 'inventario_bajo',
            'mensaje': f"Bajo stock de '{item.producto}': quedan {item.cantidad} {item.unidad}.",
            'url': url_for('inventario')
        })

    return alertas

# Rutas principales
@app.route('/')
def home():
    return render_template('presentacion.html')

@app.route('/dashboard')
@login_required
def index():
    user_id = session['user_id']
    # Ensure empleado table has expected columns before running queries
    # ensure_empleado_columns()
    if 'finca_id' not in session:
        # Dashboard global si no hay finca seleccionada
        total_fincas = Finca.query.filter_by(usuario_id=user_id).count()
        total_animales = db.session.query(db.func.count(Animal.id)).join(Finca).filter(Finca.usuario_id == user_id).scalar()
        total_empleados = db.session.query(db.func.count(Empleado.id)).join(Finca).filter(Finca.usuario_id == user_id).scalar()
        total_potreros = db.session.query(db.func.count(Potrero.id)).join(Finca).filter(Finca.usuario_id == user_id).scalar()
        
        # Gráfico de animales por finca
        animales_por_finca = db.session.query(Finca.nombre, db.func.count(Animal.id)).join(Animal, Animal.finca_id == Finca.id).filter(Finca.usuario_id == user_id).group_by(Finca.nombre).order_by(Finca.nombre).all()
        finca_labels = [row[0] for row in animales_por_finca]
        finca_data = [row[1] for row in animales_por_finca]
        
        # Actividad Reciente Global (ultimos 5 animales en todas las fincas)
        animales_recientes = Animal.query.join(Finca).filter(Finca.usuario_id == user_id).order_by(Animal.id.desc()).limit(5).all()

        return render_template('index.html', 
                               no_finca=True,
                               total_fincas=total_fincas,
                               total_animales=total_animales,
                               total_empleados=total_empleados,
                               total_potreros=total_potreros,
                               finca_labels=finca_labels,
                               finca_data=finca_data,
                               animales_recientes=animales_recientes,
                               # KPIs (None for global view)
                               vaca_top_produccion=None,
                               vaca_top_leche=0,
                               today=date.today(),
                               date=date
                               )

    finca_id = session.get('finca_id')
    finca = Finca.query.get_or_404(finca_id)

    # Recopilar alertas para la finca
    alertas = get_finca_alertas(finca_id)

    # Estadísticas para la finca seleccionada
    total_animales = Animal.query.filter_by(finca_id=finca_id).count()
    total_potreros = Potrero.query.filter_by(finca_id=finca_id).count()
    # Use raw SQL count for empleados to avoid ORM selecting all columns (which fails if DB not migrated)
    try:
        total_empleados = db.session.execute(text("SELECT count(*) FROM empleado WHERE finca_id = :fid"), {"fid": finca_id}).scalar() or 0
    except SAOperationalError:
        # attempt to ensure columns then retry once
        # ensure_empleado_columns()
        total_empleados = db.session.execute(text("SELECT count(*) FROM empleado WHERE finca_id = :fid"), {"fid": finca_id}).scalar() or 0
    total_vacunas = Vacuna.query.filter_by(finca_id=finca_id).count()
    
    # --- Datos de Partos ---
    # Contar vacas que ya parieron
    vacas_parieron = db.session.query(db.func.count(db.func.distinct(Parto.animal_id)))\
        .join(Animal, Parto.animal_id == Animal.id)\
        .filter(Animal.finca_id == finca_id)\
        .scalar() or 0
    
    # Contar vacas preñadas (por parir)
    vacas_preñadas = db.session.query(db.func.count(db.func.distinct(DiagnosticoPrenez.animal_id)))\
        .join(Animal, DiagnosticoPrenez.animal_id == Animal.id)\
        .filter(
            Animal.finca_id == finca_id,
            DiagnosticoPrenez.resultado == 'preñada',
            Animal.tipo == 'vaca'
        )\
        .scalar() or 0
    
    # --- Datos de Rendimiento y Finanzas ---
    
    # 1. Valor total del inventario
    valor_total_inventario = db.session.query(
        db.func.sum(Inventario.cantidad * Inventario.precio_unitario)
    ).filter(Inventario.finca_id == finca_id).scalar() or 0.0

    # 2. KPIs
    # KPI: Alertas del mes
    hoy = date.today()
    alertas_mes = len(alertas) if alertas else 0
    
    # KPI: Eventos de salud del mes (ya no se usa en dashboard)
    eventos_salud_mes = db.session.query(EventoSalud).filter(
        EventoSalud.animal_id.in_(
            db.session.query(Animal.id).filter(Animal.finca_id == finca_id)
        ),
        db.func.extract('month', EventoSalud.fecha_evento) == hoy.month,
        db.func.extract('year', EventoSalud.fecha_evento) == hoy.year
    ).count()
    
    # KPI: Vaca con más producción del mes
    
    # Encontrar la vaca con mayor producción este mes
    vaca_top_query = db.session.query(
        Animal, db.func.sum(Produccion.cantidad).label('total_leche')
    ).join(
        Produccion, Animal.id == Produccion.animal_id
    ).filter(
        Animal.finca_id == finca_id,
        Animal.tipo == 'vaca',
        Animal.estado == 'activo',
        Produccion.tipo_produccion == 'leche',
        db.func.extract('month', Produccion.fecha) == hoy.month,
        db.func.extract('year', Produccion.fecha) == hoy.year
    ).group_by(
        Animal.id
    ).order_by(
        db.desc('total_leche')
    ).first()
    
    if vaca_top_query:
        vaca_top_produccion, vaca_top_leche = vaca_top_query
    else:
        vaca_top_produccion = None
        vaca_top_leche = 0

    # 3. Producción reciente
    AnimalAlias = aliased(Animal)
    produccion_reciente = db.session.query(
        Produccion, AnimalAlias.identificacion
    ).join(
        AnimalAlias, Produccion.animal_id == AnimalAlias.id
    ).filter(
        Produccion.finca_id == finca_id
    ).order_by(Produccion.fecha.desc()).limit(5).all()

    # --- Fin de Datos de Rendimiento ---

    # --- Datos para la columna lateral ---

    # Carga de potreros
    potreros = Potrero.query.filter_by(finca_id=finca_id).order_by(Potrero.nombre).all()
    potreros_carga = []
    for p in potreros:
        ocupantes = Animal.query.filter_by(potrero_id=p.id).count()
        carga_percent = (ocupantes / p.capacidad * 100) if p.capacidad > 0 else 0
        
        if carga_percent > 90:
            color = 'danger'
        elif carga_percent > 70:
            color = 'warning'
        else:
            color = 'success'

        potreros_carga.append({
            'nombre': p.nombre,
            'ocupantes': ocupantes,
            'capacidad': p.capacidad,
            'carga_percent': round(carga_percent, 1),
            'color': color
        })

    # Bajo inventario para widget dedicado
    bajo_inventario_items = Inventario.query.filter(
        Inventario.finca_id == finca_id,
        Inventario.cantidad < 10 # Umbral para 'bajo stock'
    ).order_by(Inventario.cantidad).limit(5).all()

    return render_template('index.html', 
                           no_finca=False,
                           finca_actual=finca,
                           alertas=alertas,
                           total_animales=total_animales,
                           total_potreros=total_potreros,
                           total_empleados=total_empleados,
                           total_vacunas=total_vacunas,
                           # Nuevos datos de rendimiento
                           valor_total_inventario=valor_total_inventario,
                           produccion_reciente=produccion_reciente,
                           alertas_mes=alertas_mes,
                           # KPIs
                           vaca_top_produccion=vaca_top_produccion,
                           vaca_top_leche=vaca_top_leche,
                           # Datos de la columna lateral
                           potreros_carga=potreros_carga,
                           bajo_inventario_items=bajo_inventario_items,
                           today=date.today(),
                           date=date
                           )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if user.estado == 'activo':
                login_user(user)  # Usar Flask-Login
                session['user_id'] = user.id  # Mantener para compatibilidad
                session['username'] = user.username
                flash(f'Bienvenido administrador', 'success')
                return redirect(url_for('index'))
            else:
                flash('Tu cuenta está inactiva. Contacta al administrador.', 'error')
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()  # Usar Flask-Login
    session.clear()
    return redirect(url_for('login'))

# Rutas para autenticación con Google
@app.route('/login/google')
def login_google():
    """Inicia el flujo de OAuth con Google"""
    if not google.client_id:
        flash('La autenticación con Google no está configurada.', 'error')
        return redirect(url_for('login'))
    
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
def google_callback():
    """Recibe la respuesta de Google OAuth"""
    try:
        token = google.authorize_access_token()
        resp = google.get('userinfo')
        user_info = resp.json()
        
        google_id = user_info.get('id')
        email = user_info.get('email')
        nombre = user_info.get('given_name', '')
        apellido = user_info.get('family_name', '')
        
        # Buscar usuario por google_id
        user = Usuario.query.filter_by(google_id=google_id).first()
        
        if not user:
            # Buscar por email
            user = Usuario.query.filter_by(email=email).first()
            
            if user:
                # Actualizar usuario existente con google_id
                user.google_id = google_id
                db.session.commit()
            else:
                # Crear nuevo usuario
                username = email.split('@')[0]
                base_username = username
                counter = 1
                
                # Asegurar username único
                while Usuario.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = Usuario(
                    username=username,
                    email=email,
                    nombre=nombre or username,
                    apellido=apellido or '',
                    google_id=google_id,
                    telefono='',
                    estado='activo',
                    rol='usuario'
                )
                db.session.add(user)
                db.session.commit()
                
                flash('Cuenta creada exitosamente con Google.', 'success')
        
        # Iniciar sesión
        login_user(user)
        session['user_id'] = user.id
        session['username'] = user.username
        flash(f'Bienvenido {user.nombre}', 'success')
        return redirect(url_for('index'))
        
    except OAuthError as e:
        flash(f'Error al autenticar con Google: {str(e)}', 'error')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f'Error inesperado: {str(e)}', 'error')
        return redirect(url_for('login'))

# Ruta para olvidé mi contraseña
@app.route('/forgot-password', methods=['GET', 'POST'])
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Por favor ingresa tu correo electrónico.', 'error')
            return render_template('auth/forgot_password.html')
        
        # Buscar usuario por email
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            # Generar código numérico de 6 dígitos
            codigo = ''.join(secrets.choice(string.digits) for _ in range(6))
            fecha_expiracion = datetime.utcnow() + timedelta(hours=1)

            # Guardar código en la base de datos
            reset_token = PasswordResetToken(
                usuario_id=usuario.id,
                token=codigo,
                fecha_expiracion=fecha_expiracion
            )
            
            try:
                db.session.add(reset_token)
                db.session.commit()

                # Enviar email con el código de recuperación
                if enviar_email_recuperacion(usuario, codigo):
                    flash('Te hemos enviado un código de recuperación a tu correo electrónico. Revísalo e introdúcelo a continuación.', 'success')
                else:
                    flash('No se pudo enviar el correo de recuperación. Por favor, contacta al administrador.', 'warning')

                # Guardar email en sesión para usarlo en la pantalla de código
                session['reset_email'] = email
                
            except Exception as e:
                db.session.rollback()
                print(f"[ERROR] Error al crear código de recuperación: {e}")
                flash('Ocurrió un error al procesar tu solicitud. Inténtalo de nuevo.', 'error')
        else:
            # Por seguridad, mostrar el mismo mensaje aunque el email no exista
            flash('Si el correo está registrado, se enviará un código de recuperación.', 'info')
        
        return redirect(url_for('reset_password_code'))
    
    return render_template('auth/forgot_password.html')

@app.route('/reset-password-code', methods=['GET', 'POST'])
def reset_password_code():
    """Pantalla para introducir email y código de recuperación"""
    if request.method == 'POST':
        # El email viene desde la sesión, no del formulario
        email = session.get('reset_email', '').strip()
        codigo = request.form.get('codigo', '').strip()

        # Validaciones básicas
        if not email:
            flash('Debes ingresar primero tu correo en la pantalla de recuperación.', 'error')
            return redirect(url_for('forgot_password'))

        if not codigo:
            flash('Por favor ingresa el código de recuperación.', 'error')
            return render_template('auth/reset_password_code.html')

        try:
            usuario = Usuario.query.filter_by(email=email).first()
            if not usuario:
                flash('Correo o código inválido.', 'error')
                return render_template('auth/reset_password_code.html', email=email)

            # Buscar código válido para ese usuario
            reset_token = PasswordResetToken.query.filter_by(
                usuario_id=usuario.id,
                token=codigo,
                usado=False
            ).first()

            if not reset_token:
                flash('Código de recuperación inválido o ya utilizado.', 'error')
                return render_template('auth/reset_password_code.html', email=email)

            if datetime.utcnow() > reset_token.fecha_expiracion:
                flash('El código de recuperación ha expirado. Solicita uno nuevo.', 'error')
                return render_template('auth/reset_password_code.html', email=email)

            # Guardar en sesión quién ha verificado el código
            session['reset_user_id'] = usuario.id
            session['reset_token_id'] = reset_token.id

            flash('Código verificado correctamente. Ahora define tu nueva contraseña.', 'success')
            return redirect(url_for('reset_password_new'))

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Error al verificar código de recuperación: {e}")
            flash('Ocurrió un error al verificar el código. Inténtalo de nuevo.', 'error')
            return render_template('auth/reset_password_code.html', email=email)

    # GET
    return render_template('auth/reset_password_code.html')

@app.route('/reset-password-new', methods=['GET', 'POST'])
def reset_password_new():
    """Pantalla para definir nueva contraseña después de verificar el código"""
    user_id = session.get('reset_user_id')
    token_id = session.get('reset_token_id')

    if not user_id or not token_id:
        flash('Primero debes verificar tu código de recuperación.', 'error')
        return redirect(url_for('forgot_password'))

    usuario = db.session.get(Usuario, user_id)
    reset_token = db.session.get(PasswordResetToken, token_id)

    if not usuario or not reset_token or reset_token.usado:
        flash('El código de recuperación ya fue utilizado o no es válido.', 'error')
        return redirect(url_for('forgot_password'))

    if datetime.utcnow() > reset_token.fecha_expiracion:
        flash('El código de recuperación ha expirado. Solicita uno nuevo.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not password or not confirm_password:
            flash('Por favor completa ambos campos de contraseña.', 'error')
            return render_template('auth/reset_password_new.html')

        if password != confirm_password:
            flash('Las contraseñas no coinciden. Por favor, inténtalo de nuevo.', 'error')
            return render_template('auth/reset_password_new.html')

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return render_template('auth/reset_password_new.html')

        try:
            usuario.password_hash = generate_password_hash(password)
            reset_token.usado = True
            db.session.commit()

            # Limpiar datos de la sesión de recuperación
            session.pop('reset_user_id', None)
            session.pop('reset_token_id', None)

            flash('Tu contraseña ha sido actualizada exitosamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Error al actualizar contraseña después de verificar código: {e}")
            flash('Ocurrió un error al actualizar tu contraseña. Inténtalo de nuevo.', 'error')
            return render_template('auth/reset_password_new.html')

    # GET
    return render_template('auth/reset_password_new.html')

# Ruta para registro público de usuarios
@app.route('/registro', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validaciones
        if not all([username, email, password]):
            flash('Todos los campos obligatorios deben ser completados.', 'error')
            return render_template('registro.html')
        
        # Validar que las contraseñas coincidan
        if password != confirm_password:
            flash('Las contraseñas no coinciden. Por favor, inténtalo de nuevo.', 'error')
            return render_template('registro.html')
        
        # Validar longitud de contraseña
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return render_template('registro.html')
        
        # Verificar que el username y email no existan
        if Usuario.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe. Elige otro.', 'error')
            return render_template('registro.html')
        
        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado. Usa otro email.', 'error')
            return render_template('registro.html')
        
        try:
            # Crear nuevo usuario
            nuevo_usuario = Usuario(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                nombre=username,  # Usar username como nombre por defecto
                apellido='',  # Campo vacío
                telefono='',  # Campo vacío
                direccion='',  # Campo vacío
                rol='usuario'  # Por defecto es usuario normal
            )
            
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            flash('¡Registro exitoso! Ya puedes iniciar sesión con tus credenciales.', 'success')
            return redirect(url_for('login'))
        
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Error al registrar usuario: {e}")
            flash('Ocurrió un error al registrar el usuario. Inténtalo de nuevo.', 'error')
            return render_template('registro.html')
    
    return render_template('registro.html')

# Alias para compatibilidad
register = registro

# Ruta para gestión de usuarios (solo admin)
@app.route('/usuarios')
@login_required
def usuarios():
    if current_user.rol != 'admin':
        flash('No tienes permiso para acceder a esta sección', 'danger')
        return redirect(url_for('index'))
    
    usuarios = Usuario.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

# API Endpoints para resúmenes del dashboard
# NOTE: ruta antigua renombrada para evitar conflicto con `api_resumen_animales`.
@app.route('/api/resumen/animales_old')
@login_required
def resumen_animales():
    try:
        # Obtener la finca del usuario actual
        finca = Finca.query.filter_by(usuario_id=current_user.id).first()
        if not finca:
            return jsonify({
                'error': 'No se encontró la finca del usuario',
                'total_animales': 0,
                'promedio_edad': 0,
                'por_tipo': []
            }), 404

        # Contar animales por tipo
        animales_por_tipo = db.session.query(
            Animal.tipo,
            db.func.count(Animal.id).label('cantidad')
        ).filter(
            Animal.finca_id == finca.id,
            Animal.estado == 'activo'
        ).group_by(Animal.tipo).all()

        # Calcular promedio de edad
        hoy = date.today()
        animales = Animal.query.filter_by(finca_id=finca.id, estado='activo').all()
        edades = []
        for animal in animales:
            if animal.fecha_nacimiento:
                edad = (hoy - animal.fecha_nacimiento).days / 365.25
                edades.append(edad)
        
        promedio_edad = round(sum(edades) / len(edades), 1) if edades else 0

        return jsonify({
            'total_animales': len(animales),
            'promedio_edad': promedio_edad,
            'por_tipo': [{'tipo': tipo, 'cantidad': cantidad} for tipo, cantidad in animales_por_tipo]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/usuarios/editar/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(usuario_id):
    # Verificar que el usuario sea admin
    if current_user.rol != 'admin':
        flash('No tienes permisos para acceder a esta sección', 'error')
        return redirect(url_for('index'))
    
    usuario = Usuario.query.get_or_404(usuario_id)
    
    if request.method == 'POST':
        # Debug temporal - imprimir todos los campos del formulario
        print("🔍 DEBUG - Campos del formulario:")
        for key, value in request.form.items():
            print(f"  {key}: {value}")
        
        usuario.nombre = request.form['nombre']
        usuario.apellido = request.form['apellido']
        usuario.telefono = request.form['telefono']
        usuario.email = request.form['email']
        usuario.direccion = request.form.get('direccion', '')
        usuario.estado = request.form['estado']
        
        # Manejar el campo rol de forma segura
        nuevo_rol = request.form.get('rol')
        print(f"🔍 DEBUG - Rol recibido: '{nuevo_rol}' (usuario: {usuario.username})")
        
        if nuevo_rol:
            usuario.rol = nuevo_rol
        elif usuario.username == 'admin':
            # Mantener rol admin si no se envía el campo
            usuario.rol = 'admin'
        else:
            # Valor por defecto para usuarios normales
            usuario.rol = 'usuario'
            
        print(f"🔍 DEBUG - Rol asignado: '{usuario.rol}'")
        
        # Si se proporciona una nueva contraseña, actualizarla
        nueva_password = request.form.get('nueva_password')
        if nueva_password:
            usuario.password_hash = generate_password_hash(nueva_password)
            flash('Usuario actualizado exitosamente. Nueva contraseña asignada.', 'success')
        else:
            flash('Usuario actualizado exitosamente', 'success')
        
        db.session.commit()
        return redirect(url_for('usuarios'))
    
    return render_template('editar_usuario.html', usuario=usuario)

@app.route('/usuarios/eliminar/<int:usuario_id>', methods=['POST'])
@login_required
def eliminar_usuario(usuario_id):
    # Verificar que el usuario sea admin
    if current_user.rol != 'admin':
        flash('No tienes permisos para acceder a esta sección', 'error')
        return redirect(url_for('index'))
    
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # No permitir eliminar al admin principal
    if usuario.username == 'admin':
        flash('No se puede eliminar al administrador principal', 'error')
        return redirect(url_for('usuarios'))
    
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado exitosamente', 'success')
    return redirect(url_for('usuarios'))

@app.route('/animal/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_animal():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar', 'warning')
        return redirect(url_for('fincas'))

    potreros = Potrero.query.filter_by(finca_id=session['finca_id']).all()
    ubicaciones = Ubicacion.query.filter_by(finca_id=session['finca_id']).all()
    animales = Animal.query.filter_by(finca_id=session['finca_id']).filter(Animal.estado.in_(['activo'])).all()

    if request.method == 'POST':
        identificacion = request.form['identificacion']
        # Validación de unicidad
        animal_existente = Animal.query.filter(
            Animal.finca_id == session['finca_id'],
            db.func.lower(Animal.identificacion) == db.func.lower(identificacion)
        ).first()
        if animal_existente:
            flash(f'El ID de animal "{identificacion}" ya existe en esta finca. Por favor, utiliza uno diferente.', 'danger')
            return render_template('nuevo_animal.html', potreros=potreros, animales=animales, form_data=request.form)
        
        filename = None
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_folder = app.config['UPLOAD_FOLDER']
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                file.save(os.path.join(upload_folder, filename))
        
        # Procesar ubicación seleccionada
        ubicacion_seleccionada = request.form.get('ubicacion_id')
        potrero_id = None
        ubicacion_id = None
        
        if ubicacion_seleccionada:
            if ubicacion_seleccionada.startswith('potrero_'):
                potrero_id = int(ubicacion_seleccionada.replace('potrero_', ''))
            elif ubicacion_seleccionada.startswith('ubicacion_'):
                ubicacion_id = int(ubicacion_seleccionada.replace('ubicacion_', ''))
        
        # Crear el animal con todos los campos adicionales
        animal = Animal(
            identificacion=identificacion,
            nombre=request.form.get('nombre'),
            tipo=request.form['tipo'],
            raza=request.form['raza'],
            fecha_nacimiento=datetime.strptime(request.form['fecha_nacimiento'], '%Y-%m-%d').date(),
            peso=float(request.form['peso_actual']),
            peso_nacimiento=float(request.form['peso_nacimiento']) if request.form.get('peso_nacimiento') else None,
            estado=request.form.get('estado', 'activo'),
            potrero_id=potrero_id,
            ubicacion_id=ubicacion_id,
            imagen=filename,
            finca_id=session['finca_id'],
            padre_id=parse_int(request.form.get('padre_id')),
            madre_id=parse_int(request.form.get('madre_id')),
            sexo=request.form.get('sexo'),
            color_señas=request.form.get('color_señas'),
            ubicacion_actual=request.form.get('ubicacion_actual'),
            numero_crias_camada=int(request.form['numero_crias_camada']) if request.form.get('numero_crias_camada') else None,
            peso_promedio_crias=float(request.form['peso_promedio_crias']) if request.form.get('peso_promedio_crias') else None,
            produccion_diaria=float(request.form['produccion_diaria']) if request.form.get('produccion_diaria') else None,
            unidad_produccion=request.form.get('unidad_produccion'),
            observaciones=request.form.get('observaciones')
        )
        
        db.session.add(animal)
        db.session.commit()
        
        
        # Registrar historial de potrero si se asignó
        if animal.potrero_id:
            historial_potrero = HistorialPotrero(
                animal_id=animal.id,
                potrero_id=animal.potrero_id,
                motivo='Asignación inicial'
            )
            db.session.add(historial_potrero)
        
        db.session.commit()
        flash('Animal registrado exitosamente', 'success')
        return redirect(url_for('animales'))
    
    # Siempre pasar form_data, aunque sea vacío
    return render_template('nuevo_animal.html', potreros=potreros, ubicaciones=ubicaciones, animales=animales, form_data={})

@app.route('/animal/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_animal(id):
    animal = Animal.query.get_or_404(id)
    # Asegurarse de que el animal pertenece a la finca activa en la sesión
    if animal.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('animales'))

    potreros = Potrero.query.filter_by(finca_id=session['finca_id']).all()
    ubicaciones = Ubicacion.query.filter_by(finca_id=session['finca_id']).all()

    if request.method == 'POST':
        # Validación de unicidad para la identificación (excluyendo el propio animal)
        nueva_identificacion = request.form['identificacion']
        animal_existente = Animal.query.filter(
            Animal.finca_id == session['finca_id'],
            db.func.lower(Animal.identificacion) == db.func.lower(nueva_identificacion),
            Animal.id != id
        ).first()

        if animal_existente:
            flash(f'El ID de animal "{nueva_identificacion}" ya está en uso. Por favor, utiliza uno diferente.', 'danger')
            return render_template('editar_animal.html', animal=animal, potreros=potreros, form_data=request.form)

        animal.identificacion = nueva_identificacion
        animal.tipo = request.form['tipo']
        animal.raza = request.form['raza']
        animal.fecha_nacimiento = datetime.strptime(request.form['fecha_nacimiento'], '%Y-%m-%d').date()
        animal.peso = float(request.form['peso'])
        animal.estado = request.form['estado']
        
        # Procesar ubicación seleccionada (igual que en nuevo_animal)
        ubicacion_seleccionada = request.form.get('ubicacion_id')
        potrero_anterior = animal.potrero_id
        ubicacion_anterior = animal.ubicacion_id
        
        animal.potrero_id = None
        animal.ubicacion_id = None
        
        if ubicacion_seleccionada:
            if ubicacion_seleccionada.startswith('potrero_'):
                animal.potrero_id = int(ubicacion_seleccionada.replace('potrero_', ''))
            elif ubicacion_seleccionada.startswith('ubicacion_'):
                animal.ubicacion_id = int(ubicacion_seleccionada.replace('ubicacion_', ''))
        
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Asegurarse que el directorio de subida existe
                upload_folder = app.config['UPLOAD_FOLDER']
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                file.save(os.path.join(upload_folder, filename))
                animal.imagen = filename  # Guardar solo el nombre del archivo

        db.session.commit()
        # Registrar historial de potrero si cambió
        if animal.potrero_id and animal.potrero_id != potrero_anterior:
            historial_potrero = HistorialPotrero(
                animal_id=animal.id,
                potrero_id=animal.potrero_id,
                motivo='Cambio de potrero desde edición'
            )
            db.session.add(historial_potrero)
            db.session.commit()
        flash('Animal actualizado exitosamente', 'success')
        return redirect(url_for('animales'))
    
    return render_template('editar_animal.html', animal=animal, potreros=potreros, ubicaciones=ubicaciones)

# Rutas para Potreros (solo para bovinos)
@app.route('/potreros')
@login_required
def potreros():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    # Asegurar que la columna imagen exista
    # ensure_potrero_columns()
    
    finca_id = session['finca_id']
    potreros = Potrero.query.filter_by(finca_id=finca_id).all()
    
    # Contar animales por potrero
    animales_por_potrero = {}
    for potrero in potreros:
        animales_por_potrero[potrero.id] = Animal.query.filter_by(potrero_id=potrero.id).count()
    
    return render_template('potreros.html', potreros=potreros, animales_por_potrero=animales_por_potrero)

# Rutas para Cochiqueras (solo para cerdos)
@app.route('/cochiqueras')
@login_required
def cochiqueras():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
    cochiqueras = Ubicacion.query.filter_by(
        finca_id=session['finca_id'], 
        tipo_ubicacion='cochiquera'
    ).all()
    animales_porcinos = Animal.query.filter_by(finca_id=session['finca_id']).filter(
        Animal.tipo.in_(['Porcino', 'porcino', 'cerdo', 'cochino'])
    ).filter(Animal.estado.in_(['activo'])).all()
    
    # Calcular ocupación de cada cochiquera
    animales_por_cochiquera = {}
    for cochiquera in cochiqueras:
        # Contar animales asignados a esta cochiquera
        animales_en_cochiquera = Animal.query.filter_by(
            finca_id=session['finca_id'], 
            ubicacion_id=cochiquera.id
        ).filter(Animal.estado.in_(['activo'])).all()
        animales_por_cochiquera[cochiquera.id] = len(animales_en_cochiquera)
    
    return render_template('cochiqueras.html', 
                         cochiqueras=cochiqueras, 
                         animales=animales_porcinos, 
                         animales_por_cochiquera=animales_por_cochiquera)

@app.route('/gallineros')
@login_required
def gallineros():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    gallineros = Ubicacion.query.filter_by(
        finca_id=session['finca_id'], 
        tipo_ubicacion='gallinero'
    ).all()
    animales_aviar = Animal.query.filter_by(finca_id=session['finca_id']).filter(
        Animal.tipo.in_(['Aviar', 'aviar', 'gallina', 'pollo', 'gallo'])
    ).filter(Animal.estado.in_(['activo'])).all()
    
    # Calcular ocupación de cada gallinero
    animales_por_gallinero = {}
    for gallinero in gallineros:
        animales_por_gallinero[gallinero.id] = sum(1 for a in animales_aviar if a.ubicacion_id == gallinero.id)
    
    return render_template('gallineros.html', 
                         gallineros=gallineros, 
                         animales=animales_aviar, 
                         animales_por_gallinero=animales_por_gallinero)

# Rutas para Establos/Corrales (para caballos y otros equinos)
@app.route('/establos')
@login_required
def establos():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    establos = Ubicacion.query.filter_by(
        finca_id=session['finca_id']
    ).filter(
        Ubicacion.tipo_ubicacion.in_(['establo', 'corral'])
    ).all()
    animales_equinos = Animal.query.filter_by(finca_id=session['finca_id']).filter(
        Animal.tipo.in_(['Equino', 'equino', 'caballo', 'yegua'])
    ).all()
    
    # Calcular ocupación de cada establo
    animales_por_establo = {}
    for establo in establos:
        animales_por_establo[establo.id] = sum(1 for a in animales_equinos if a.ubicacion_id == establo.id)
    
    return render_template('establos.html', 
                         establos=establos, 
                         animales=animales_equinos, 
                         animales_por_establo=animales_por_establo)

@app.route('/potrero/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_potrero():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    if request.method == 'POST':
        # Debug: Print form data
        print("Form data received:", request.form)
        print("Form files:", request.files)
        # Manejar subida de imagen
        imagen_filename = None
        if 'imagen' in request.files:
            imagen = request.files['imagen']
            if imagen and imagen.filename != '':
                # Validar que sea una imagen
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                if '.' in imagen.filename and imagen.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Generar nombre único
                    filename = secure_filename(imagen.filename)
                    unique_filename = f"potrero_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    imagen_path = os.path.join('static', 'imagenes_potreros', unique_filename)
                    
                    # Crear directorio si no existe
                    os.makedirs(os.path.dirname(imagen_path), exist_ok=True)
                    
                    # Guardar imagen
                    imagen.save(imagen_path)
                    imagen_filename = unique_filename
        
        # Debug: Print all form fields and files
        print("\n=== FORM DATA ===")
        print("Form fields:", request.form.to_dict())
        print("Form files:", request.files.to_dict())
        print("Session finca_id:", session.get('finca_id'))
        
        # Get form data with validation
        nombre = request.form.get('nombre', '').strip()
        area = float(request.form.get('area', 0))
        capacidad = int(request.form.get('capacidad', 0))
        estado = request.form.get('estado', 'disponible')
        funcion = request.form.get('funcion')
        tipo_pasto = request.form.get('tipo_pasto', '').strip()
        
        # Validate required fields
        if not funcion:
            # If funcion is not in the form data, check if 'otra_funcion' is provided
            funcion = request.form.get('otra_funcion', 'pastoreo')
            print(f"Using 'otra_funcion' value: {funcion}")
        
        print("\n=== PROCESSED VALUES ===")
        print(f"Nombre: {nombre}")
        print(f"Area: {area}")
        print(f"Capacidad: {capacidad}")
        print(f"Estado: {estado}")
        print(f"Funcion: {funcion}")
        print(f"Tipo pasto: {tipo_pasto}")
        print(f"Imagen: {imagen_filename}")
        print(f"Finca ID: {session.get('finca_id')}")
        
        # Create potrero with validated data
        potrero = Potrero(
            nombre=nombre,
            area=area,
            capacidad=capacidad,
            estado=estado,
            funcion=funcion or 'pastoreo',  # Fallback to 'pastoreo' if still None
            tipo_pasto=tipo_pasto,
            imagen=imagen_filename,
            finca_id=session['finca_id']
        )
        db.session.add(potrero)
        db.session.commit()
        flash('Potrero creado exitosamente', 'success')
        return redirect(url_for('potreros'))
    return render_template('nuevo_potrero.html')

@app.route('/potrero/editar/<int:potrero_id>', methods=['GET', 'POST'])
@login_required
def editar_potrero(potrero_id):
    potrero = Potrero.query.get_or_404(potrero_id)
    if potrero.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('potreros'))
    if request.method == 'POST':
        potrero.nombre = request.form['nombre']
        potrero.area = float(request.form['area'])
        potrero.capacidad = int(request.form['capacidad'])
        potrero.estado = request.form['estado']
        potrero.funcion = request.form['funcion']
        
        # Verificar si se debe eliminar la imagen actual
        if request.form.get('remove_image') == 'true':
            if potrero.imagen:
                old_imagen_path = os.path.join('static', 'imagenes_potreros', potrero.imagen)
                if os.path.exists(old_imagen_path):
                    os.remove(old_imagen_path)
                potrero.imagen = None
        
        # Manejar subida de nueva imagen
        if 'imagen' in request.files:
            imagen = request.files['imagen']
            if imagen and imagen.filename != '':
                # Validar que sea una imagen
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                if '.' in imagen.filename and imagen.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Eliminar imagen anterior si existe
                    if potrero.imagen:
                        old_imagen_path = os.path.join('static', 'imagenes_potreros', potrero.imagen)
                        if os.path.exists(old_imagen_path):
                            os.remove(old_imagen_path)
                    
                    # Generar nombre único
                    filename = secure_filename(imagen.filename)
                    unique_filename = f"potrero_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    imagen_path = os.path.join('static', 'imagenes_potreros', unique_filename)
                    
                    # Crear directorio si no existe
                    os.makedirs(os.path.dirname(imagen_path), exist_ok=True)
                    
                    # Guardar imagen
                    imagen.save(imagen_path)
                    potrero.imagen = unique_filename
        
        db.session.commit()
        flash('Potrero actualizado exitosamente', 'success')
        return redirect(url_for('potreros'))
    return render_template('editar_potrero.html', potrero=potrero)

@app.route('/potrero/<int:potrero_id>/eliminar', methods=['GET', 'POST'])
@login_required
def eliminar_potrero(potrero_id):
    potrero = Potrero.query.get_or_404(potrero_id)
    if potrero.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('potreros'))
    
    if request.method == 'POST':
        # Verificar si hay animales asignados
        animales_asignados = Animal.query.filter_by(potrero_id=potrero_id).count()
        if animales_asignados > 0:
            flash(f'No se puede eliminar el potrero porque tiene {animales_asignados} animales asignados', 'danger')
            return redirect(url_for('potreros'))
        
        db.session.delete(potrero)
        db.session.commit()
        flash('Potrero eliminado exitosamente', 'success')
        return redirect(url_for('potreros'))
    
    return render_template('eliminar_potrero.html', potrero=potrero)

# Rutas para Ubicaciones
@app.route('/ubicacion/nueva', methods=['GET', 'POST'])
@login_required
def nueva_ubicacion():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar', 'warning')
        return redirect(url_for('fincas'))
    
    if request.method == 'POST':
        # Handle image upload
        imagen_filename = None
        if 'imagen' in request.files:
            imagen = request.files['imagen']
            if imagen and imagen.filename != '':
                # Validate that it's an image
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                if '.' in imagen.filename and imagen.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Generate unique filename
                    filename = secure_filename(imagen.filename)
                    unique_filename = f"ubicacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    imagen_path = os.path.join('static', 'imagenes_ubicaciones', unique_filename)
                    
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(imagen_path), exist_ok=True)
                    
                    # Save image
                    imagen.save(imagen_path)
                    imagen_filename = unique_filename
        
        # Create the location with the image
        ubicacion = Ubicacion(
            nombre=request.form['nombre'],
            tipo_ubicacion=request.form['tipo_ubicacion'],
            tipo_animal=request.form['tipo_animal'],
            capacidad=int(request.form['capacidad']),
            area=float(request.form['area']) if request.form.get('area') else None,
            descripcion=request.form.get('descripcion'),
            imagen=imagen_filename,  # Save the image filename
            finca_id=session['finca_id']
        )
        
        db.session.add(ubicacion)
        db.session.commit()
        
        # Redirect to the appropriate page based on the location type
        tipo = request.form['tipo_ubicacion']
        if tipo == 'gallinero':
            return redirect(url_for('gallineros'))
        elif tipo == 'cochiquera':
            return redirect(url_for('cochiqueras'))
        else:
            return redirect(url_for('potreros'))
    
    return render_template('nueva_ubicacion.html')

@app.route('/ubicacion/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_ubicacion(id):
    ubicacion = Ubicacion.query.get_or_404(id)
    if ubicacion.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('potreros'))
    
    if request.method == 'POST':
        # Handle image deletion if checkbox is checked
        if 'eliminar_imagen' in request.form and request.form['eliminar_imagen'] == 'on':
            if ubicacion.imagen:
                old_imagen_path = os.path.join('static', 'imagenes_ubicaciones', ubicacion.imagen)
                if os.path.exists(old_imagen_path):
                    os.remove(old_imagen_path)
                ubicacion.imagen = None
        # Handle new image upload if provided
        elif 'imagen' in request.files:
            imagen = request.files['imagen']
            if imagen and imagen.filename != '':
                # Validate that it's an image
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                if '.' in imagen.filename and imagen.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Delete old image if exists
                    if ubicacion.imagen:
                        old_imagen_path = os.path.join('static', 'imagenes_ubicaciones', ubicacion.imagen)
                        if os.path.exists(old_imagen_path):
                            os.remove(old_imagen_path)
                    
                    # Generate unique filename
                    filename = secure_filename(imagen.filename)
                    unique_filename = f"ubicacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    imagen_path = os.path.join('static', 'imagenes_ubicaciones', unique_filename)
                    
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(imagen_path), exist_ok=True)
                    
                    # Save new image
                    imagen.save(imagen_path)
                    ubicacion.imagen = unique_filename
        
        # Update other fields
        ubicacion.nombre = request.form['nombre']
        ubicacion.tipo_ubicacion = request.form['tipo_ubicacion']
        ubicacion.tipo_animal = request.form['tipo_animal']
        ubicacion.capacidad = int(request.form['capacidad'])
        ubicacion.area = float(request.form['area']) if request.form.get('area') else None
        ubicacion.descripcion = request.form.get('descripcion')
        ubicacion.estado = request.form['estado']
        
        db.session.commit()
        flash('Ubicación actualizada exitosamente', 'success')
        
        # Redirect to the appropriate page based on the location type
        tipo = request.form['tipo_ubicacion']
        if tipo == 'gallinero':
            return redirect(url_for('gallineros'))
        elif tipo == 'cochiquera':
            return redirect(url_for('cochiqueras'))
        else:
            return redirect(url_for('potreros'))
    
    return render_template('editar_ubicacion.html', ubicacion=ubicacion)

@app.route('/ubicacion/<int:id>/eliminar', methods=['GET', 'POST'])
@login_required
def eliminar_ubicacion(id):
    ubicacion = Ubicacion.query.get_or_404(id)
    if ubicacion.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('potreros'))
    
    if request.method == 'POST':
        # Verificar si hay animales asignados
        animales_asignados = Animal.query.filter_by(ubicacion_id=id).count()
        if animales_asignados > 0:
            flash(f'No se puede eliminar la ubicación porque tiene {animales_asignados} animales asignados', 'danger')
            
            # Redirigir según el tipo de ubicación
            if ubicacion.tipo_ubicacion == 'gallinero':
                return redirect(url_for('gallineros'))
            elif ubicacion.tipo_ubicacion == 'cochiquera':
                return redirect(url_for('cochiqueras'))
            else:
                return redirect(url_for('potreros'))
        
        # Eliminar la imagen asociada si existe
        if ubicacion.imagen:
            imagen_path = os.path.join('static', 'imagenes_ubicaciones', ubicacion.imagen)
            if os.path.exists(imagen_path):
                os.remove(imagen_path)
        
        # Eliminar la ubicación
        db.session.delete(ubicacion)
        db.session.commit()
        
        flash('Ubicación eliminada exitosamente', 'success')
        
        # Redirigir según el tipo de ubicación
        if ubicacion.tipo_ubicacion == 'gallinero':
            return redirect(url_for('gallineros'))
        elif ubicacion.tipo_ubicacion == 'cochiquera':
            return redirect(url_for('cochiqueras'))
        else:
            return redirect(url_for('potreros'))
    
    return render_template('eliminar_ubicacion.html', ubicacion=ubicacion)

# Rutas para Vacunas
@app.route('/vacunas')
@login_required
def vacunas():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    # Obtener parámetros de filtrado
    animal_id = request.args.get('animal_id', '').strip()
    estado_vacuna = request.args.get('estado_vacuna', '').strip()
    fecha_desde = request.args.get('fecha_desde', '').strip()
    
    # Construir la consulta base
    query = Vacuna.query.filter_by(finca_id=session['finca_id'])
    
    # Aplicar filtros si están presentes
    if animal_id:
        # Buscar animales que coincidan con el ID
        animales = Animal.query.filter(
            Animal.finca_id == session['finca_id'],
            Animal.identificacion.ilike(f'%{animal_id}%')
        ).all()
        if animales:
            animal_ids = [a.id for a in animales]
            query = query.filter(Vacuna.animal_id.in_(animal_ids))
        else:
            # Si no hay coincidencias, retornar vacío
            query = query.filter(Vacuna.id == -1)
    
    if estado_vacuna:
        query = query.filter(Vacuna.estado == estado_vacuna)
    
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            query = query.filter(Vacuna.fecha_aplicacion >= fecha_desde_obj)
        except ValueError:
            pass  # Ignorar fecha inválida
    
    # Ordenar y obtener resultados
    vacunas = query.order_by(Vacuna.fecha_proxima.asc()).all()
    
    return render_template('vacunas.html', vacunas=vacunas, today=date.today())

@app.route('/vacuna/<int:vacuna_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_vacuna(vacuna_id):
    vacuna = Vacuna.query.get_or_404(vacuna_id)
    if vacuna.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('vacunas'))
    
    if request.method == 'POST':
        vacuna.tipo_vacuna = request.form['tipo_vacuna']
        if request.form.get('otra_vacuna'):
            vacuna.tipo_vacuna = request.form['otra_vacuna']
        vacuna.fecha_aplicacion = datetime.strptime(request.form['fecha_aplicacion'], '%Y-%m-%d').date()
        vacuna.fecha_proxima = datetime.strptime(request.form['fecha_proxima'], '%Y-%m-%d').date()
        vacuna.observaciones = request.form['observaciones']
        vacuna.aplicada_por = request.form['aplicada_por']
        vacuna.empleado_id = int(request.form['empleado_id']) if request.form.get('empleado_id') else None
        vacuna.numero_lote = request.form.get('numero_lote')
        if request.form.get('fecha_vencimiento'):
            vacuna.fecha_vencimiento = datetime.strptime(request.form['fecha_vencimiento'], '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Vacuna actualizada exitosamente', 'success')
        return redirect(url_for('vacunas'))
    
    animales = Animal.query.filter_by(finca_id=session['finca_id']).filter(Animal.estado.in_(['activo'])).all()
    veterinarios = Empleado.query.filter(Empleado.finca_id == session['finca_id'], Empleado.cargo.like('%veterinario%')).all()
    return render_template('editar_vacuna.html', vacuna=vacuna, animales=animales, veterinarios=veterinarios)

@app.route('/vacuna/<int:vacuna_id>/eliminar', methods=['POST'])
@login_required
def eliminar_vacuna(vacuna_id):
    vacuna = Vacuna.query.get_or_404(vacuna_id)
    if vacuna.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('vacunas'))
    db.session.delete(vacuna)
    db.session.commit()
    flash('Vacuna eliminada exitosamente', 'success')
    return redirect(url_for('vacunas'))

@app.route('/vacunas/<int:vacuna_id>/marcar_completada', methods=['POST'])
@login_required
def marcar_vacuna_completada(vacuna_id):
    """Mark a vaccine as completed (change from vencida to aplicada)"""
    if 'finca_id' not in session:
        return jsonify({'success': False, 'message': 'No hay finca seleccionada'}), 400
    
    vacuna = Vacuna.query.get_or_404(vacuna_id)
    
    # Verify the vaccine belongs to the user's farm
    if vacuna.finca_id != session.get('finca_id'):
        return jsonify({'success': False, 'message': 'Acción no autorizada'}), 403
    
    # Update vaccine status to aplicada
    vacuna.estado = 'aplicada'
    
    try:
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'Vacuna marcada como aplicada exitosamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Error al actualizar la vacuna: {str(e)}'
        }), 500

# En la ruta nueva_vacuna, permitir seleccionar el veterinario desde empleados
@app.route('/vacuna/nueva', methods=['GET', 'POST'])
@login_required
def nueva_vacuna():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    if request.method == 'POST':
        tipo_vacuna = request.form['tipo_vacuna']
        if request.form.get('otra_vacuna'):
            tipo_vacuna = request.form['otra_vacuna']
        
        # Obtener el nombre del empleado seleccionado
        empleado_id = request.form.get('empleado_id')
        nombre_aplicador = ""
        if empleado_id:
            empleado = Empleado.query.get(empleado_id)
            if empleado:
                nombre_aplicador = f"{empleado.nombre} {empleado.apellido}"
        
        vacuna = Vacuna(
            animal_id=int(request.form['animal_id']),
            tipo_vacuna=tipo_vacuna,
            fecha_aplicacion=datetime.strptime(request.form['fecha_aplicacion'], '%Y-%m-%d').date(),
            fecha_proxima=datetime.strptime(request.form['fecha_proxima'], '%Y-%m-%d').date(),
            observaciones=request.form['observaciones'],
            aplicada_por=nombre_aplicador,
            finca_id=session['finca_id'],
            empleado_id=int(empleado_id) if empleado_id else None,
            estado=request.form['estado']
        )
        db.session.add(vacuna)
        db.session.commit()
        flash('Vacuna registrada exitosamente')
        return redirect(url_for('vacunas'))
    animales = Animal.query.filter_by(finca_id=session['finca_id']).filter(Animal.estado.in_(['activo'])).all()
    veterinarios = Empleado.query.filter(Empleado.finca_id == session['finca_id'], Empleado.cargo.like('%veterinario%')).all()
    return render_template('nueva_vacuna.html', animales=animales, veterinarios=veterinarios)

# Rutas para Maquinaria
@app.route('/maquinaria')
@login_required
def maquinaria():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    # Asegurar que la columna imagen exista
    # ensure_maquinaria_columns()
    
    maquinarias = Maquinaria.query.filter_by(finca_id=session['finca_id']).all()
    
    # Calcular estadísticas para las tarjetas
    total_maquinaria = len(maquinarias)
    operativas = len([m for m in maquinarias if m.estado == 'operativo'])
    en_mantenimiento = len([m for m in maquinarias if m.estado == 'en_mantenimiento'])
    fuera_servicio = len([m for m in maquinarias if m.estado == 'fuera_servicio'])
    
    return render_template('maquinaria.html', 
                         maquinarias=maquinarias,
                         total_maquinaria=total_maquinaria,
                         operativas=operativas,
                         en_mantenimiento=en_mantenimiento,
                         fuera_servicio=fuera_servicio)

@app.route('/maquinaria/nueva', methods=['GET', 'POST'])
@login_required
def nueva_maquinaria():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar', 'warning')
        return redirect(url_for('fincas'))

    if request.method == 'POST':
        try:
            nombre = request.form['nombre']
            tipo = request.form['tipo']
            marca = request.form.get('marca')
            modelo = request.form.get('modelo')
            numero_serie = request.form.get('numero_serie')
            año_fabricacion = request.form.get('año_fabricacion')
            fecha_adquisicion = request.form.get('fecha_adquisicion')
            valor_compra = request.form.get('valor_compra')
            estado = request.form.get('estado', 'operativo')
            ubicacion_actual = request.form.get('ubicacion_actual')
            horas_uso = request.form.get('horas_uso', 0)
            responsable = request.form.get('responsable')
            observaciones = request.form.get('observaciones')

            # Manejar la carga de imagen
            filename = None
            if 'imagen' in request.files:
                file = request.files['imagen']
                if file and file.filename != '' and allowed_file(file.filename):
                    # Generar nombre único para la imagen
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(UPLOAD_MAQUINARIA, unique_filename)
                    file.save(file_path)
                    filename = unique_filename

            # Convertir fechas y números
            if fecha_adquisicion:
                fecha_adquisicion = datetime.strptime(fecha_adquisicion, '%Y-%m-%d').date()
            if año_fabricacion:
                año_fabricacion = int(año_fabricacion)
            if valor_compra:
                valor_compra = float(valor_compra)
            if horas_uso:
                horas_uso = float(horas_uso)

            nueva_maquina = Maquinaria(
                finca_id=session['finca_id'],
                nombre=nombre,
                tipo=tipo,
                marca=marca,
                modelo=modelo,
                numero_serie=numero_serie,
                año_fabricacion=año_fabricacion,
                fecha_adquisicion=fecha_adquisicion,
                valor_compra=valor_compra,
                estado=estado,
                ubicacion_actual=ubicacion_actual,
                horas_uso=horas_uso,
                responsable=responsable,
                observaciones=observaciones,
                imagen=filename
            )

            db.session.add(nueva_maquina)
            db.session.commit()
            flash('Maquinaria registrada exitosamente', 'success')
            return redirect(url_for('maquinaria'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar la maquinaria: {str(e)}', 'danger')

    return render_template('nueva_maquinaria.html')

@app.route('/maquinaria/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_maquinaria(id):
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar', 'warning')
        return redirect(url_for('fincas'))

    maquina = Maquinaria.query.filter_by(id=id, finca_id=session['finca_id']).first_or_404()

    if request.method == 'POST':
        try:
            maquina.nombre = request.form['nombre']
            maquina.tipo = request.form['tipo']
            maquina.marca = request.form.get('marca')
            maquina.modelo = request.form.get('modelo')
            maquina.numero_serie = request.form.get('numero_serie')
            año_fabricacion = request.form.get('año_fabricacion')
            fecha_adquisicion = request.form.get('fecha_adquisicion')
            valor_compra = request.form.get('valor_compra')
            maquina.estado = request.form.get('estado')
            maquina.ubicacion_actual = request.form.get('ubicacion_actual')
            horas_uso = request.form.get('horas_uso')
            maquina.responsable = request.form.get('responsable')
            maquina.observaciones = request.form.get('observaciones')

            # Manejar la carga de imagen
            if 'imagen' in request.files:
                file = request.files['imagen']
                if file and file.filename != '' and allowed_file(file.filename):
                    # Eliminar imagen anterior si existe
                    if maquina.imagen:
                        old_image_path = os.path.join(UPLOAD_MAQUINARIA, maquina.imagen)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    
                    # Generar nombre único para la nueva imagen
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(UPLOAD_MAQUINARIA, unique_filename)
                    file.save(file_path)
                    maquina.imagen = unique_filename

            # Manejar eliminación de imagen
            if request.form.get('eliminar_imagen') == '1':
                if maquina.imagen:
                    old_image_path = os.path.join(UPLOAD_MAQUINARIA, maquina.imagen)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                    maquina.imagen = None

            # Convertir fechas y números
            if fecha_adquisicion:
                maquina.fecha_adquisicion = datetime.strptime(fecha_adquisicion, '%Y-%m-%d').date()
            else:
                maquina.fecha_adquisicion = None
            if año_fabricacion:
                maquina.año_fabricacion = int(año_fabricacion)
            else:
                maquina.año_fabricacion = None
            if valor_compra:
                maquina.valor_compra = float(valor_compra)
            else:
                maquina.valor_compra = None
            if horas_uso:
                maquina.horas_uso = float(horas_uso)
            else:
                maquina.horas_uso = 0

            db.session.commit()
            flash('Maquinaria actualizada exitosamente', 'success')
            return redirect(url_for('maquinaria'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la maquinaria: {str(e)}', 'danger')

    return render_template('editar_maquinaria.html', maquina=maquina)

@app.route('/maquinaria/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_maquinaria(id):
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar', 'warning')
        return redirect(url_for('fincas'))

    maquina = Maquinaria.query.filter_by(id=id, finca_id=session['finca_id']).first_or_404()

    try:
        db.session.delete(maquina)
        db.session.commit()
        flash('Maquinaria eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la maquinaria: {str(e)}', 'danger')

    return redirect(url_for('maquinaria'))

@app.route('/maquinaria/reporte')
@login_required
def reporte_maquinaria():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    maquinarias = Maquinaria.query.filter_by(finca_id=session['finca_id']).all()
    finca = Finca.query.get(session['finca_id'])
    
    # Calcular estadísticas
    total_maquinaria = len(maquinarias)
    total_valor = sum(m.valor_compra or 0 for m in maquinarias)
    operativas = len([m for m in maquinarias if m.estado == 'operativo'])
    en_mantenimiento = len([m for m in maquinarias if m.estado == 'en_mantenimiento'])
    fuera_servicio = len([m for m in maquinarias if m.estado == 'fuera_servicio'])
    
    # Agrupar por tipo
    tipos = {}
    for m in maquinarias:
        tipos[m.tipo] = tipos.get(m.tipo, 0) + 1
    
    return render_template('reporte_maquinaria.html', 
                         maquinarias=maquinarias, 
                         finca=finca,
                         total_maquinaria=total_maquinaria,
                         total_valor=total_valor,
                         operativas=operativas,
                         en_mantenimiento=en_mantenimiento,
                         fuera_servicio=fuera_servicio,
                         tipos=tipos)

@app.route('/maquinaria/reporte/pdf')
@login_required
def reporte_maquinaria_pdf():
    """Genera un reporte PDF de maquinaria con el mismo estilo que los demás reportes"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.lib import colors
        from io import BytesIO
        
        finca_id = session['finca_id']
        finca = Finca.query.get(finca_id)
        
        # Obtener datos de maquinaria
        maquinarias = Maquinaria.query.filter_by(finca_id=finca_id).order_by(Maquinaria.tipo, Maquinaria.nombre).all()
        
        # Calcular estadísticas
        total_maquinaria = len(maquinarias)
        total_valor = sum(m.valor_compra or 0 for m in maquinarias)
        operativas = len([m for m in maquinarias if m.estado == 'operativo'])
        en_mantenimiento = len([m for m in maquinarias if m.estado == 'en_mantenimiento'])
        fuera_servicio = len([m for m in maquinarias if m.estado == 'fuera_servicio'])
        
        # Agrupar por tipo
        tipos = {}
        for m in maquinarias:
            tipos[m.tipo] = tipos.get(m.tipo, 0) + 1
        
        # Crear PDF en orientación landscape para más espacio
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        
        # Colores
        color_primario = colors.HexColor('#1a365d')
        color_secundario = colors.HexColor('#4a5568')
        
        # Estilos
        titulo_style = ParagraphStyle(
            'Titulo',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            textColor=color_primario,
            fontName='Helvetica-Bold',
            spaceAfter=10
        )
        
        subtitulo_style = ParagraphStyle(
            'Subtitulo',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=color_secundario,
            spaceAfter=20
        )
        
        elements = []
        
        # Título
        elements.append(Paragraph("REPORTE DE MAQUINARIA", titulo_style))
        
        # Info de finca
        finca_texto = finca.nombre.upper() if finca else "FINCA"
        elements.append(Paragraph(finca_texto, subtitulo_style))
        
        # Fecha
        fecha_actual = datetime.now()
        fecha_texto = "Generado el " + fecha_actual.strftime('%d/%m/%Y a las %H:%M')
        elements.append(Paragraph(fecha_texto, subtitulo_style))
        elements.append(Spacer(1, 15))
        
        # Tabla de resumen
        resumen_data = [
            ['TOTAL MÁQUINAS', 'OPERATIVAS', 'EN MANTENIMIENTO', 'FUERA SERVICIO'],
            [str(total_maquinaria), str(operativas), str(en_mantenimiento), str(fuera_servicio)]
        ]
        
        resumen_table = Table(resumen_data, colWidths=[doc.width*0.22, doc.width*0.22, doc.width*0.22, doc.width*0.22])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), color_primario),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, 1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f7fafc')),
        ]))
        elements.append(resumen_table)
        elements.append(Spacer(1, 25))
        
        # Tabla de maquinaria detallada
        data = [['NOMBRE', 'TIPO', 'MARCA/MODELO', 'AÑO', 'ESTADO', 'UBICACIÓN', 'RESPONSABLE']]
        
        for maquina in maquinarias:
            marca_modelo = f"{maquina.marca or ''}{' / ' if maquina.marca and maquina.modelo else ''}{maquina.modelo or ''}"
            if not marca_modelo.strip():
                marca_modelo = 'N/A'
            
            # Determinar color de estado
            if maquina.estado == 'operativo':
                estado_texto = 'OPERATIVO'
            elif maquina.estado == 'en_mantenimiento':
                estado_texto = 'EN MANTENIMIENTO'
            elif maquina.estado == 'fuera_servicio':
                estado_texto = 'FUERA SERVICIO'
            else:
                estado_texto = maquina.estado.upper()
            
            data.append([
                maquina.nombre,
                maquina.tipo.title(),
                marca_modelo,
                str(maquina.año_fabricacion) if maquina.año_fabricacion else 'N/A',
                estado_texto,
                maquina.ubicacion_actual or 'N/A',
                maquina.responsable or 'N/A'
            ])
        
        # Crear tabla
        col_widths = [
            doc.width*0.25,  # Nombre
            doc.width*0.13,  # Tipo
            doc.width*0.17,  # Marca/Modelo
            doc.width*0.07,  # Año
            doc.width*0.13,  # Estado
            doc.width*0.13,  # Ubicación
            doc.width*0.12,  # Responsable
        ]
        
        tabla = Table(data, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), color_primario),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            
            # Datos
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, color_primario),
            
            # Alternar colores de fila
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        # Colorear estados
        for i, maquina in enumerate(maquinarias, start=1):
            if maquina.estado == 'operativo':
                bg_color = colors.HexColor('#c6f6d5')  # Verde claro
            elif maquina.estado == 'en_mantenimiento':
                bg_color = colors.HexColor('#feebc8')  # Naranja claro
            elif maquina.estado == 'fuera_servicio':
                bg_color = colors.HexColor('#fed7d7')  # Rojo claro
            else:
                bg_color = colors.HexColor('#e2e8f0')  # Gris claro
            
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (4, i), (4, i), bg_color),  # Columna de estado (índice 4)
            ]))
        
        elements.append(tabla)
        elements.append(Spacer(1, 20))
        
        # Distribución por tipo si hay tipos
        if tipos:
            elements.append(Paragraph("DISTRIBUCIÓN POR TIPO", titulo_style))
            elements.append(Spacer(1, 10))
            
            tipos_data = [['TIPO', 'CANTIDAD', 'PORCENTAJE']]
            for tipo, cantidad in sorted(tipos.items()):
                porcentaje = (cantidad / total_maquinaria * 100) if total_maquinaria > 0 else 0
                tipos_data.append([
                    tipo.title(),
                    str(cantidad),
                    "{:.1f}%".format(porcentaje)
                ])
            
            tipos_table = Table(tipos_data, colWidths=[doc.width*0.6, doc.width*0.2, doc.width*0.2])
            tipos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), color_primario),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('LINEBELOW', (0, 0), (-1, 0), 1.5, color_primario),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(tipos_table)
            elements.append(Spacer(1, 20))
        
        # Pie de página
        pie_texto = (finca.nombre if finca else 'Empresa') + " - Sistema de Gestión Agropecuaria"
        pie_style = ParagraphStyle(
            'Pie',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#a0aec0')
        )
        elements.append(Paragraph(pie_texto, pie_style))
        
        # Generar PDF
        doc.build(elements)
        
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name='Reporte_Maquinaria_' + (finca.nombre if finca else 'Finca').replace(' ', '_') + '_' + fecha_actual.strftime('%Y%m%d') + '.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Error al generar el reporte PDF: {str(e)}', 'danger')
        return redirect(url_for('maquinaria'))

# Rutas para Empleados
@app.route('/empleados')
@login_required
def empleados():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    empleados = Empleado.query.filter_by(finca_id=session['finca_id']).all()
    return render_template('empleados.html', empleados=empleados, today=date.today())

@app.route('/empleado/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_empleado():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    if request.method == 'POST':
        cargo = request.form.get('cargo')
        if request.form.get('otro_cargo'):
            cargo = request.form.get('otro_cargo')

        fecha_contratacion = None
        if request.form.get('fecha_contratacion'):
            fecha_contratacion = datetime.strptime(request.form['fecha_contratacion'], '%Y-%m-%d').date()

        fecha_ingreso = None
        if request.form.get('fecha_ingreso'):
            fecha_ingreso = datetime.strptime(request.form['fecha_ingreso'], '%Y-%m-%d').date()

        empleado = Empleado(
            cedula=request.form.get('cedula'),
            nombre=request.form.get('nombre'),
            apellido=request.form.get('apellido'),
            telefono=request.form.get('telefono'),
            direccion=request.form.get('direccion'),
            cargo=cargo,
            fecha_contratacion=fecha_contratacion or datetime.utcnow().date(),
            salario=float(request.form.get('salario') or 0),
            finca_id=session['finca_id'],
            nacionalidad=( 'Venezolano' if request.form.get('cedula_pref') == 'V' else ('Extranjero' if request.form.get('cedula_pref') == 'EX' else request.form.get('nacionalidad'))),
            condiciones_enfermedades=request.form.get('condiciones_enfermedades'),
            referencia_personal=request.form.get('referencia_personal'),
            referencia_file=None,
            alergico_medicamento=bool(request.form.get('alergico_medicamento')),
            alergias_medicamento=request.form.get('alergias_medicamento'),
            fecha_ingreso=fecha_ingreso
        )

        # Save files if provided
        foto = request.files.get('foto_empleado')
        if foto and allowed_file(foto.filename):
            fname = secure_filename(f"empl_{empleado.cedula}_{int(datetime.utcnow().timestamp())}_{foto.filename}")
            dest = os.path.join(UPLOAD_EMPLEADOS, fname)
            foto.save(dest)
            empleado.foto_empleado = os.path.join('static', 'uploads', 'empleados', fname).replace('\\', '/')

        cedula_file = request.files.get('foto_cedula')
        if cedula_file and allowed_file(cedula_file.filename):
            fname = secure_filename(f"ced_{empleado.cedula}_{int(datetime.utcnow().timestamp())}_{cedula_file.filename}")
            dest = os.path.join(UPLOAD_CEDULAS, fname)
            cedula_file.save(dest)
            empleado.foto_cedula = os.path.join('static', 'uploads', 'cedulas', fname).replace('\\', '/')

        # referencia file
        referencia = request.files.get('referencia_file')
        if referencia and allowed_file(referencia.filename):
            fname = secure_filename(f"ref_{empleado.cedula}_{int(datetime.utcnow().timestamp())}_{referencia.filename}")
            dest = os.path.join(UPLOAD_REFERENCIAS, fname)
            referencia.save(dest)
            empleado.referencia_file = os.path.join('static', 'uploads', 'referencias', fname).replace('\\', '/')

        db.session.add(empleado)
        db.session.commit()
        flash('Empleado registrado exitosamente')
        return redirect(url_for('empleados'))
    
    return render_template('nuevo_empleado.html')

@app.route('/empleado/editar/<int:empleado_id>', methods=['GET', 'POST'])
@login_required
def editar_empleado(empleado_id):
    empleado = Empleado.query.get_or_404(empleado_id)
    if empleado.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('empleados'))
    if request.method == 'POST':
        empleado.nombre = request.form.get('nombre')
        empleado.apellido = request.form.get('apellido')
        empleado.cedula = request.form.get('cedula')
        empleado.telefono = request.form.get('telefono')
        empleado.direccion = request.form.get('direccion')
        cargo = request.form.get('cargo')
        if request.form.get('otro_cargo'):
            cargo = request.form.get('otro_cargo')
        empleado.cargo = cargo
        if request.form.get('fecha_contratacion'):
            empleado.fecha_contratacion = datetime.strptime(request.form['fecha_contratacion'], '%Y-%m-%d').date()
        empleado.salario = float(request.form.get('salario') or 0)
        empleado.estado = request.form.get('estado', 'activo')
        empleado.descripcion = request.form.get('descripcion')
        # Prefer cedula prefix selector for nationality if provided
        pref = request.form.get('cedula_pref')
        if pref == 'V':
            empleado.nacionalidad = 'Venezolano'
        elif pref == 'EX':
            empleado.nacionalidad = 'Extranjero'
        else:
            empleado.nacionalidad = request.form.get('nacionalidad')
        empleado.condiciones_enfermedades = request.form.get('condiciones_enfermedades')
        empleado.referencia_personal = request.form.get('referencia_personal')
        # Checkbox may be missing if unchecked
        empleado.alergico_medicamento = bool(request.form.get('alergico_medicamento'))
        empleado.alergias_medicamento = request.form.get('alergias_medicamento')
        if request.form.get('fecha_ingreso'):
            empleado.fecha_ingreso = datetime.strptime(request.form['fecha_ingreso'], '%Y-%m-%d').date()

        # Handle files
        foto = request.files.get('foto_empleado')
        if foto and allowed_file(foto.filename):
            fname = secure_filename(f"empl_{empleado.cedula}_{int(datetime.utcnow().timestamp())}_{foto.filename}")
            dest = os.path.join(UPLOAD_EMPLEADOS, fname)
            foto.save(dest)
            empleado.foto_empleado = os.path.join('static', 'uploads', 'empleados', fname).replace('\\', '/')

        cedula_file = request.files.get('foto_cedula')
        if cedula_file and allowed_file(cedula_file.filename):
            fname = secure_filename(f"ced_{empleado.cedula}_{int(datetime.utcnow().timestamp())}_{cedula_file.filename}")
            dest = os.path.join(UPLOAD_CEDULAS, fname)
            cedula_file.save(dest)
            empleado.foto_cedula = os.path.join('static', 'uploads', 'cedulas', fname).replace('\\', '/')

        # referencia file update
        referencia = request.files.get('referencia_file')
        if referencia and allowed_file(referencia.filename):
            fname = secure_filename(f"ref_{empleado.cedula}_{int(datetime.utcnow().timestamp())}_{referencia.filename}")
            dest = os.path.join(UPLOAD_REFERENCIAS, fname)
            referencia.save(dest)
            empleado.referencia_file = os.path.join('static', 'uploads', 'referencias', fname).replace('\\', '/')

        db.session.commit()
        flash('Empleado actualizado exitosamente', 'success')
        return redirect(url_for('empleados'))
    return render_template('editar_empleado.html', empleado=empleado)

@app.route('/empleado/<int:empleado_id>/eliminar', methods=['POST'])
@login_required
def eliminar_empleado(empleado_id):
    empleado = Empleado.query.get_or_404(empleado_id)
    if empleado.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('empleados'))
    db.session.delete(empleado)
    db.session.commit()
    flash('Empleado eliminado exitosamente', 'success')
    return redirect(url_for('empleados'))

@app.route('/empleado/<int:empleado_id>/carta_trabajo')
@login_required
def carta_trabajo_pdf(empleado_id):
    """Genera una carta de trabajo profesional y corporativa"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
        from reportlab.lib import colors
        from io import BytesIO
        
        empleado = Empleado.query.get_or_404(empleado_id)
        finca = Finca.query.get(session['finca_id'])
        
        if empleado.finca_id != session['finca_id']:
            flash('No tienes permiso para generar esta carta', 'danger')
            return redirect(url_for('empleados'))
        
        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        
        # Colores corporativos
        color_primario = colors.HexColor('#1a365d')  # Azul oscuro
        color_secundario = colors.HexColor('#4a5568')  # Gris
        color_acento = colors.HexColor('#2b6cb0')  # Azul medio
        
        # Estilos
        titulo_empresa = ParagraphStyle(
            'TituloEmpresa',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=4,
            alignment=TA_CENTER,
            textColor=color_primario,
            fontName='Helvetica-Bold'
        )
        
        subtitulo_empresa = ParagraphStyle(
            'SubtituloEmpresa',
            parent=styles['Normal'],
            fontSize=8,
            spaceAfter=2,
            alignment=TA_CENTER,
            textColor=color_secundario,
            fontName='Helvetica'
        )
        
        titulo_documento = ParagraphStyle(
            'TituloDocumento',
            parent=styles['Heading2'],
            fontSize=12,
            spaceBefore=15,
            spaceAfter=15,
            alignment=TA_CENTER,
            textColor=color_primario,
            fontName='Helvetica-Bold',
            leading=14
        )
        
        texto_normal = ParagraphStyle(
            'TextoNormal',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            fontName='Helvetica',
            textColor=colors.HexColor('#2d3748')
        )
        
        etiqueta_style = ParagraphStyle(
            'Etiqueta',
            parent=styles['Normal'],
            fontSize=8,
            leading=11,
            fontName='Helvetica-Bold',
            textColor=color_secundario
        )
        
        valor_style = ParagraphStyle(
            'Valor',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            fontName='Helvetica',
            textColor=colors.HexColor('#1a202c')
        )
        
        elements = []
        
        # HEADER
        if finca:
            elements.append(Paragraph(finca.nombre.upper(), titulo_empresa))
            
            if finca.direccion:
                elements.append(Paragraph(finca.direccion, subtitulo_empresa))
            contacto_parts = []
            if finca.telefono:
                contacto_parts.append("Tel: " + finca.telefono)
            if finca.email:
                contacto_parts.append(finca.email)
            if contacto_parts:
                elements.append(Paragraph(" | ".join(contacto_parts), subtitulo_empresa))
        else:
            elements.append(Paragraph("EMPRESA AGRÍCOLA Y GANADERA", titulo_empresa))
        
        # Línea decorativa
        elements.append(Spacer(1, 4))
        line_data = [['']]
        line_table = Table(line_data, colWidths=[doc.width])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, 0), 2, color_primario),
        ]))
        elements.append(line_table)
        
        # TÍTULO
        elements.append(Paragraph("CERTIFICADO DE TRABAJO", titulo_documento))
        
        # FECHA
        fecha_actual = datetime.now()
        ciudad = finca.ubicacion if finca and finca.ubicacion else ''
        fecha_texto = ciudad + ", " + fecha_actual.strftime('%d de %B de %Y') if ciudad else fecha_actual.strftime('%d de %B de %Y')
        
        fecha_style = ParagraphStyle(
            'Fecha',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_RIGHT,
            spaceAfter=12,
            textColor=color_secundario
        )
        elements.append(Paragraph(fecha_texto, fecha_style))
        elements.append(Spacer(1, 8))
        
        # CUERPO
        finca_nombre = finca.nombre if finca else 'la empresa'
        intro = "A quien corresponda:<br/><br/>Por medio del presente documento, <b>" + finca_nombre + "</b> certifica que:"
        elements.append(Paragraph(intro, texto_normal))
        elements.append(Spacer(1, 8))
        
        # DATOS PRINCIPALES DEL EMPLEADO
        nombre_completo = empleado.nombre + " " + empleado.apellido
        cargo_actual = empleado.cargo if empleado.cargo else 'No especificado'
        
        # Calcular antigüedad
        antiguedad_texto = ""
        if empleado.fecha_contratacion:
            from datetime import date
            hoy = date.today()
            dias = (hoy - empleado.fecha_contratacion).days
            años = dias // 365
            meses = (dias % 365) // 30
            
            if años > 0 and meses > 0:
                antiguedad_texto = str(años) + " años y " + str(meses) + " meses"
            elif años > 0:
                antiguedad_texto = str(años) + " años"
            elif meses > 0:
                antiguedad_texto = str(meses) + " meses"
            else:
                antiguedad_texto = str(dias) + " días"
        
        fecha_ingreso = empleado.fecha_contratacion.strftime('%d/%m/%Y') if empleado.fecha_contratacion else 'No registrada'
        
        # Tabla de datos principales
        datos_data = [
            [Paragraph('EMPLEADO:', etiqueta_style), Paragraph(nombre_completo.upper(), valor_style)],
            [Paragraph('DOCUMENTO:', etiqueta_style), Paragraph(empleado.cedula, valor_style)],
            [Paragraph('CARGO:', etiqueta_style), Paragraph(cargo_actual.upper(), valor_style)],
            [Paragraph('FECHA DE INGRESO:', etiqueta_style), Paragraph(fecha_ingreso, valor_style)],
        ]
        
        if antiguedad_texto:
            datos_data.append([Paragraph('ANTIGÜEDAD:', etiqueta_style), Paragraph(antiguedad_texto, valor_style)])
        
        datos_table = Table(datos_data, colWidths=[doc.width*0.30, doc.width*0.60])
        datos_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(datos_table)
        elements.append(Spacer(1, 12))
        
        # TEXTO DE FUNCIONES
        funciones_texto = "Durante su tiempo en la organización, el(la) empleado(a) se ha desempeñado en el área de <b>" + cargo_actual + "</b>, realizando las actividades propias de su cargo con responsabilidad y compromiso."
        elements.append(Paragraph(funciones_texto, texto_normal))
        elements.append(Spacer(1, 6))
        
        # ESTADO Y SALARIO
        estado_laboral = empleado.estado.upper() if empleado.estado else 'ACTIVO'
        salario_texto = "${:,.2f}".format(empleado.salario) if empleado.salario else "Confidencial"
        
        estado_data = [
            [Paragraph('ESTADO LABORAL:', etiqueta_style), Paragraph(estado_laboral, valor_style)],
            [Paragraph('REMUNERACIÓN MENSUAL:', etiqueta_style), Paragraph(salario_texto, valor_style)],
        ]
        
        estado_table = Table(estado_data, colWidths=[doc.width*0.30, doc.width*0.60])
        estado_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(estado_table)
        elements.append(Spacer(1, 15))
        
        # DECLARACIÓN
        declaracion = "El presente certificado se expide a solicitud del(la) interesado(a) para los fines que estime conveniente. Se declara que la información contenida en este documento es verídica y que el(la) mencionado(a) mantiene una relación laboral vigente con esta organización."
        elements.append(Paragraph(declaracion, texto_normal))
        elements.append(Spacer(1, 25))
        
        # FIRMAS
        firma_data = [
            ['_______________________________', '_______________________________'],
            ['', ''],
            [nombre_completo, finca.nombre if finca else 'REPRESENTANTE LEGAL'],
            ['C.C. ' + empleado.cedula, ''],
            ['', ''],
            ['<b>FIRMA DEL EMPLEADO</b>', '<b>FIRMA Y SELLO DE LA EMPRESA</b>'],
        ]
        
        firma_table = Table(firma_data, colWidths=[doc.width*0.45, doc.width*0.45])
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 2), (-1, 3), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TEXTCOLOR', (0, 2), (-1, 3), color_secundario),
        ]))
        elements.append(firma_table)
        elements.append(Spacer(1, 30))
        
        # FOOTER
        footer_text = "Documento generado el " + fecha_actual.strftime('%d/%m/%Y') + " | " + (finca.nombre if finca else 'Empresa')
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#a0aec0')
        )
        elements.append(Paragraph(footer_text, footer_style))
        
        # Generar PDF
        doc.build(elements)
        
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name='Certificado_Trabajo_' + empleado.apellido + '_' + empleado.cedula + '.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        import traceback
        print("[ERROR] Error al generar carta: " + str(e))
        print("[ERROR] Traceback: " + traceback.format_exc())
        flash('Error al generar la carta: ' + str(e), 'danger')
        return redirect(url_for('empleados'))


# Rutas para Producción
@app.route('/produccion')
@login_required
def produccion():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    producciones = Produccion.query.join(Animal).filter_by(finca_id=session['finca_id']).all()
    return render_template('produccion.html', producciones=producciones)

@app.route('/produccion/nueva', methods=['GET', 'POST'])
@login_required
def nueva_produccion():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    if request.method == 'POST':
        tipo_produccion = request.form['tipo_produccion']
        unidad = request.form['unidad']
        
        if request.form.get('otra_produccion'):
            tipo_produccion = request.form['otra_produccion']
        if request.form.get('otra_unidad'):
            unidad = request.form['otra_unidad']
            
        produccion = Produccion(
            animal_id=int(request.form['animal_id']),
            tipo_produccion=tipo_produccion,
            cantidad=float(request.form['cantidad']),
            unidad=unidad,
            fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
            calidad=request.form['calidad'],
            finca_id=session['finca_id']
        )
        db.session.add(produccion)
        db.session.commit()
        flash('Producción registrada exitosamente')
        return redirect(url_for('produccion'))
    
    animales = Animal.query.filter_by(finca_id=session['finca_id']).filter(Animal.estado.in_(['activo'])).all()
    return render_template('nueva_produccion.html', animales=animales)

@app.route('/produccion/reporte/pdf')
@login_required
def reporte_produccion_pdf():
    """Genera un reporte PDF de producción"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib import colors
        from io import BytesIO
        
        finca_id = session['finca_id']
        
        # Obtener datos del reporte
        finca = Finca.query.get(finca_id)
        
        # Obtener todos los registros de producción con información del animal
        producciones = db.session.query(
            Produccion.id,
            Produccion.tipo_produccion,
            Produccion.cantidad,
            Produccion.unidad,
            Produccion.fecha,
            Produccion.calidad,
            Animal.id.label('animal_id'),
            Animal.identificacion,
            Animal.nombre,
            Animal.tipo,
            Animal.raza
        )\
        .join(Animal, Produccion.animal_id == Animal.id)\
        .filter(Animal.finca_id == finca_id)\
        .order_by(Produccion.fecha.desc())\
        .all()
        
        # Agrupar producciones por tipo
        producciones_por_tipo = {}
        for produccion in producciones:
            tipo = produccion.tipo_produccion
            if tipo not in producciones_por_tipo:
                producciones_por_tipo[tipo] = []
            producciones_por_tipo[tipo].append(produccion)
        
        # Estadísticas generales
        total_producciones = len(producciones)
        total_animales_productores = len(set(p.animal_id for p in producciones))
        
        # Calcular totales por tipo
        totales_por_tipo = {}
        for tipo, lista in producciones_por_tipo.items():
            total_cantidad = sum(p.cantidad for p in lista)
            totales_por_tipo[tipo] = {
                'cantidad': total_cantidad,
                'unidad': lista[0].unidad if lista else '',
                'registros': len(lista)
            }
        
        # Crear el documento PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title=f'Reporte de Producción - {finca.nombre}'
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilo para el título
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Estilo para subtítulos
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Contenido del PDF
        elements = []
        
        # Título principal
        elements.append(Paragraph(f'Reporte de Producción - {finca.nombre}', title_style))
        elements.append(Paragraph(f'Generado el: {date.today().strftime("%d/%m/%Y")}', styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Resumen general
        elements.append(Paragraph('Resumen General', subtitle_style))
        
        resumen_data = [
            ['Total de registros de producción:', str(total_producciones)],
            ['Animales productores:', str(total_animales_productores)],
            ['Tipos de producción:', str(len(producciones_por_tipo))]
        ]
        
        resumen_table = Table(resumen_data, colWidths=[doc.width/2.0]*2)
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.HexColor('#6c757d')),
        ]))
        
        elements.append(resumen_table)
        elements.append(Spacer(1, 20))
        
        # Totales por tipo de producción
        elements.append(Paragraph('Totales por Tipo de Producción', subtitle_style))
        
        headers_tipo = ['Tipo', 'Total Producido', 'Unidad', 'Registros']
        data_tipo = [headers_tipo]
        
        for tipo, datos in totales_por_tipo.items():
            data_tipo.append([
                tipo.title(),
                f"{datos['cantidad']:.2f}",
                datos['unidad'],
                str(datos['registros'])
            ])
        
        tipo_table = Table(data_tipo, colWidths=[doc.width*0.3, doc.width*0.25, doc.width*0.2, doc.width*0.25])
        tipo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17a2b8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e3f2fd')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bbdefb')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(tipo_table)
        elements.append(Spacer(1, 20))
        
        # Detalle completo de producción
        elements.append(Paragraph('Listado Completo de Producción', subtitle_style))
        
        headers = ['Animal', 'Identificación', 'Tipo', 'Cantidad', 'Unidad', 'Fecha', 'Calidad']
        data = [headers]
        
        for produccion in producciones:
            data.append([
                produccion.tipo or 'N/A',
                produccion.identificacion,
                produccion.tipo_produccion.title(),
                f"{produccion.cantidad:.2f}",
                produccion.unidad,
                produccion.fecha.strftime('%d/%m/%Y'),
                produccion.calidad.title()
            ])
        
        produccion_table = Table(data, colWidths=[doc.width*0.15, doc.width*0.15, doc.width*0.15, doc.width*0.15, doc.width*0.1, doc.width*0.15, doc.width*0.15])
        produccion_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fff8')),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c3e6cb')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(produccion_table)
        elements.append(Spacer(1, 20))
        
        # Detalle por tipo de producción
        for tipo, lista_producciones in producciones_por_tipo.items():
            elements.append(Paragraph(f'Detalle: {tipo.title()}', subtitle_style))
            
            headers_detalle = ['Animal', 'Identificación', 'Cantidad', 'Fecha', 'Calidad']
            data_detalle = [headers_detalle]
            
            for prod in lista_producciones:
                data_detalle.append([
                    prod.tipo or 'N/A',
                    prod.identificacion,
                    f"{prod.cantidad:.2f} {prod.unidad}",
                    prod.fecha.strftime('%d/%m/%Y'),
                    prod.calidad.title()
                ])
            
            # Agregar resumen del tipo
            total_tipo = sum(p.cantidad for p in lista_producciones)
            data_detalle.append([
                'TOTAL',
                f'{len(lista_producciones)} registros',
                f'{total_tipo:.2f} {lista_producciones[0].unidad}',
                '-',
                '-'
            ])
            
            detalle_table = Table(data_detalle, colWidths=[doc.width*0.25, doc.width*0.25, doc.width*0.25, doc.width*0.15, doc.width*0.1])
            detalle_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-2, -1), colors.HexColor('#e3f2fd')),
                ('FONTSIZE', (0, 1), (-2, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bbdefb')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            # Resaltar fila de total
            detalle_table.setStyle(TableStyle([
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fff3cd')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#856404')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            
            elements.append(detalle_table)
            elements.append(Spacer(1, 20))
        
        # Generar el PDF
        doc.build(elements)
        buffer.seek(0)
        
        # Preparar respuesta
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=reporte_produccion_{date.today().strftime("%Y%m%d")}.pdf'
        
        return response
        
    except Exception as e:
        print(f"Error generando reporte PDF de producción: {e}")
        flash('Error al generar el reporte PDF', 'error')
        return redirect(url_for('produccion'))

@app.route('/produccion/editar/<int:produccion_id>', methods=['GET', 'POST'])
@login_required
def editar_produccion(produccion_id):
    produccion = Produccion.query.get_or_404(produccion_id)
    if produccion.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('produccion'))
    animales = Animal.query.filter_by(finca_id=session['finca_id']).filter(Animal.estado.in_(['activo'])).all()

@app.route('/produccion/eliminar/<int:produccion_id>', methods=['POST'])
@login_required
def eliminar_produccion(produccion_id):
    produccion = Produccion.query.get_or_404(produccion_id)
    if produccion.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('produccion'))
    
    try:
        db.session.delete(produccion)
        db.session.commit()
        flash('Registro de producción eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el registro de producción', 'error')
    
    return redirect(url_for('produccion'))

@app.route('/graficos_produccion')
@login_required
def graficos_produccion():
    if 'finca_id' not in session:
        flash('Por favor, selecciona una finca primero.', 'warning')
        return redirect(url_for('seleccion_finca'))
    
    # Obtener datos reales de producción
    from sqlalchemy import func, extract
    from datetime import datetime, date
    
    finca_id = session['finca_id']
    
    # 1. Datos de producción por tipo
    produccion_por_tipo = db.session.query(
        Produccion.tipo_produccion,
        func.sum(Produccion.cantidad).label('total'),
        func.count(Produccion.id).label('registros')
    ).filter_by(finca_id=finca_id).group_by(Produccion.tipo_produccion).all()
    
    # 2. Datos de producción mensual (últimos 12 meses)
    from datetime import date
    current_year = date.today().year
    start_date = date(current_year, 1, 1)
    
    produccion_mensual = db.session.query(
        extract('year', Produccion.fecha).label('año'),
        extract('month', Produccion.fecha).label('mes'),
        Produccion.tipo_produccion,
        func.sum(Produccion.cantidad).label('total')
    ).filter_by(finca_id=finca_id) \
    .filter(Produccion.fecha >= start_date) \
    .group_by(extract('year', Produccion.fecha), extract('month', Produccion.fecha), Produccion.tipo_produccion) \
    .order_by(extract('year', Produccion.fecha), extract('month', Produccion.fecha)) \
    .all()
    
    # 3. Producción por animal (top 10)
    produccion_por_animal = db.session.query(
        Animal.nombre,
        Animal.identificacion,
        Produccion.tipo_produccion,
        func.sum(Produccion.cantidad).label('total')
    ).join(Produccion).filter(Produccion.finca_id == finca_id) \
    .group_by(Animal.id, Produccion.tipo_produccion) \
    .order_by(func.sum(Produccion.cantidad).desc()) \
    .limit(10).all()
    
    # 4. Estadísticas generales
    stats = {
        'total_produccion': db.session.query(func.sum(Produccion.cantidad)) \
        .filter_by(finca_id=finca_id).scalar() or 0,
        'total_registros': db.session.query(func.count(Produccion.id)) \
        .filter_by(finca_id=finca_id).scalar() or 0,
        'animales_productivos': db.session.query(Produccion.animal_id) \
        .filter_by(finca_id=finca_id).distinct().count() or 0
    }
    
    # Preparar datos para los gráficos
    tipo_labels = [item.tipo_produccion for item in produccion_por_tipo]
    tipo_data = [float(item.total) for item in produccion_por_tipo]
    
    # Procesar datos mensuales
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    datasets = {}
    
    for año, mes, tipo, total in produccion_mensual:
        key = f"{tipo}"
        if key not in datasets:
            datasets[key] = [0] * 12
        datasets[key][int(mes) - 1] = float(total)
    
    mensual_datasets = []
    colores = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796']
    for i, (tipo, data) in enumerate(datasets.items()):
        mensual_datasets.append({
            'label': tipo,
            'data': data,
            'backgroundColor': colores[i % len(colores)] + '20',
            'borderColor': colores[i % len(colores)],
            'borderWidth': 2
        })
    
    return render_template('graficos_produccion.html',
                         tipo_labels=tipo_labels,
                         tipo_data=tipo_data,
                         mensual_datasets=mensual_datasets,
                         produccion_por_animal=produccion_por_animal,
                         stats=stats)

# Rutas para Eventos
@app.route('/eventos')
@login_required
def eventos():
    try:
        if 'finca_id' not in session:
            flash('Selecciona una finca para ver eventos')
            return redirect(url_for('fincas'))
        
        finca_id = session['finca_id']
        
        # Obtener todos los eventos de la finca con sus animales relacionados
        eventos = db.session.query(Evento).join(Animal).filter(
            Animal.finca_id == finca_id
        ).order_by(Evento.fecha_evento.desc()).all()
        
        # Contar eventos de tipo nota
        total_notas = len([e for e in eventos if e.tipo_evento == 'nota'])
        
        return render_template('eventos.html', eventos=eventos, total_notas=total_notas)
    
    except Exception as e:
        print(f"Error en la ruta eventos: {e}")
        flash('Error al cargar los eventos. Por favor, intenta nuevamente.')
        return render_template('eventos.html', eventos=[])

@app.route('/reporte_eventos_pdf')
@login_required
def reporte_eventos_pdf():
    """Genera un reporte PDF de eventos de animales"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib import colors
        from io import BytesIO
        
        finca_id = session['finca_id']
        finca = Finca.query.get(finca_id)
        
        # Obtener todos los eventos de la finca
        eventos = db.session.query(Evento, Animal).join(Animal).filter(
            Animal.finca_id == finca_id
        ).order_by(Evento.fecha_evento.desc()).all()
        
        # Crear el documento PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title=f'Reporte de Eventos - {finca.nombre}'
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c3e50')
        )
        
        elements = []
        
        # Título principal
        elements.append(Paragraph(f'Reporte de Eventos - {finca.nombre}', title_style))
        elements.append(Paragraph(f'Generado el: {date.today().strftime("%d/%m/%Y")}', styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Resumen
        elements.append(Paragraph('Resumen de Eventos', subtitle_style))
        
        # Contar eventos por tipo
        total_eventos = len(eventos)
        fallecidos = sum(1 for e, a in eventos if e.tipo_evento == 'fallecido')
        vendidos = sum(1 for e, a in eventos if e.tipo_evento == 'vendido')
        transferidos = sum(1 for e, a in eventos if e.tipo_evento == 'transferido')
        otros = total_eventos - fallecidos - vendidos - transferidos
        
        resumen_data = [
            ['Total de eventos:', str(total_eventos)],
            ['Animales fallecidos:', str(fallecidos)],
            ['Animales vendidos:', str(vendidos)],
            ['Animales transferidos:', str(transferidos)],
            ['Otros eventos:', str(otros)]
        ]
        
        resumen_table = Table(resumen_data, colWidths=[doc.width/2.0]*2)
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.HexColor('#6c757d')),
        ]))
        
        elements.append(resumen_table)
        elements.append(Spacer(1, 20))
        
        # Tabla detallada de eventos
        if eventos:
            elements.append(Paragraph('Detalle de Eventos', subtitle_style))
            
            data = [['Fecha', 'Animal', 'Tipo', 'Descripción', 'Responsable', 'Detalles']]
            
            for evento, animal in eventos:
                # Determinar el tipo y color
                if evento.tipo_evento == 'fallecido':
                    tipo_text = 'Fallecido'
                elif evento.tipo_evento == 'vendido':
                    tipo_text = 'Vendido'
                elif evento.tipo_evento == 'transferido':
                    tipo_text = 'Transferido'
                else:
                    tipo_text = evento.tipo_evento.title()
                
                # Detalles específicos
                detalles = '-'
                if evento.tipo_evento == 'vendido' and evento.precio_venta:
                    detalles = f"${evento.precio_venta:.2f}"
                elif evento.tipo_evento == 'fallecido' and evento.causa_muerte:
                    detalles = evento.causa_muerte[:30]
                
                data.append([
                    evento.fecha_evento.strftime('%d/%m/%Y'),
                    f"{animal.identificacion} - {animal.nombre or 'Sin nombre'}",
                    tipo_text,
                    (evento.descripcion or '-')[:40],
                    evento.responsable or '-',
                    detalles
                ])
            
            # Ajustar anchos de columna
            col_widths = [
                doc.width * 0.12,  # Fecha
                doc.width * 0.20,  # Animal
                doc.width * 0.12,  # Tipo
                doc.width * 0.25,  # Descripción
                doc.width * 0.15,  # Responsable
                doc.width * 0.16   # Detalles
            ]
            
            tabla = Table(data, colWidths=col_widths)
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(tabla)
        
        # Pie de página
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"{finca.nombre} - {finca.direccion or ''}", styles['Italic']))
        elements.append(Paragraph(f"Reporte generado el {date.today().strftime('%d/%m/%Y')} a las {datetime.now().strftime('%H:%M')}", styles['Italic']))
        
        # Generar el PDF
        def add_page_number(canvas, doc):
            page_num = canvas.getPageNumber()
            text = f"Página {page_num}"
            canvas.saveState()
            canvas.setFont('Helvetica', 9)
            canvas.drawRightString(19.5*cm, 1*cm, text)
            canvas.restoreState()
        
        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        
        # Preparar la respuesta
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'reporte_eventos_{finca.nombre.lower().replace(" ", "_")}_{date.today().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error al generar el reporte de eventos: {str(e)}")
        flash(f'Error al generar el reporte: {str(e)}', 'danger')
        return redirect(url_for('eventos'))

@app.route('/evento/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_evento():
    if 'finca_id' not in session:
        flash('Selecciona una finca para registrar un evento')
        return redirect(url_for('fincas'))
    
    finca_id = session['finca_id']
    
    if request.method == 'POST':
        try:
            animal_id = request.form['animal_id']
            tipo_evento = request.form['tipo_evento']
            fecha_evento = datetime.strptime(request.form['fecha_evento'], '%Y-%m-%d').date()
            descripcion = request.form.get('descripcion', '')
            responsable = request.form.get('responsable', '')
            
            # Verificar que el animal pertenece a la finca
            animal = Animal.query.filter_by(id=animal_id, finca_id=finca_id).first()
            if not animal:
                flash('Animal no encontrado', 'error')
                return redirect(url_for('nuevo_evento'))
            
            # Crear el evento
            evento = Evento(
                animal_id=animal_id,
                tipo_evento=tipo_evento,
                fecha_evento=fecha_evento,
                descripcion=descripcion,
                responsable=responsable
            )
            
            # Agregar campos específicos según el tipo de evento
            if tipo_evento == 'vendido':
                evento.comprador = request.form.get('comprador', '')
                evento.precio_venta = float(request.form.get('precio_venta', 0)) if request.form.get('precio_venta') else None
                # Cambiar estado del animal a 'vendido'
                animal.estado = 'vendido'
            elif tipo_evento == 'fallecido':
                evento.causa_muerte = request.form.get('causa_muerte', '')
                # Cambiar estado del animal a 'fallecido'
                animal.estado = 'fallecido'
            elif tipo_evento == 'nota':
                # Para notas, usar la descripción como contenido de la nota
                descripcion_nota = request.form.get('descripcion_nota', '')
                evento.descripcion = descripcion_nota
                # Crear también una nota en el registro completo del animal
                from app_simple import NotaAnimal
                nota_animal = NotaAnimal(
                    animal_id=animal_id,
                    nota=descripcion_nota,
                    fecha=fecha_evento
                )
                db.session.add(nota_animal)
            
            db.session.add(evento)
            db.session.commit()
            
            flash('Evento registrado exitosamente', 'success')
            return redirect(url_for('eventos'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar el evento', 'error')
            print(f"Error: {e}")
    
    # Obtener animales de la finca para el formulario
    animales = Animal.query.filter_by(finca_id=finca_id).filter(Animal.estado.in_(['activo'])).order_by(Animal.identificacion).all()
    
    return render_template('nuevo_evento.html', animales=animales, today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/evento/<int:evento_id>/eliminar', methods=['POST'])
@login_required
def eliminar_evento(evento_id):
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar', 'warning')
        return redirect(url_for('eventos'))
    
    try:
        # Obtener el evento
        evento = Evento.query.get_or_404(evento_id)
        
        # Verificar que el evento pertenezca a un animal de la finca
        animal = Animal.query.get(evento.animal_id)
        if not animal or animal.finca_id != session['finca_id']:
            flash('No tienes permiso para eliminar este evento', 'error')
            return redirect(url_for('eventos'))
        
        # Si el evento era de tipo 'fallecido' o 'vendido', restaurar el estado del animal
        if evento.tipo_evento in ['fallecido', 'vendido']:
            animal.estado = 'activo'
            db.session.add(animal)
        
        # Eliminar el evento
        db.session.delete(evento)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Evento eliminado exitosamente',
            'title': 'Evento Eliminado',
            'type': 'success'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar evento: {e}")
        return jsonify({
            'success': False,
            'message': 'Error al eliminar el evento',
            'title': 'Error',
            'type': 'error'
        })
    
@app.route('/evento/<int:evento_id>/ver')
@login_required
def ver_evento(evento_id):
    """Ver detalles de un evento"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar', 'warning')
        return redirect(url_for('eventos'))
    
    try:
        # Obtener el evento
        evento = Evento.query.get_or_404(evento_id)
        
        # Verificar que el evento pertenezca a un animal de la finca
        animal = Animal.query.get(evento.animal_id)
        if not animal or animal.finca_id != session['finca_id']:
            flash('No tienes permiso para ver este evento', 'error')
            return redirect(url_for('eventos'))
        
        return render_template('ver_evento.html', evento=evento, animal=animal, dt=datetime)
        
    except Exception as e:
        db.session.rollback()
        flash('Error al cargar el evento', 'error')
        print(f"Error al ver evento: {e}")
        return redirect(url_for('eventos'))

@app.route('/evento/<int:evento_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_evento(evento_id):
    """Editar un evento existente"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar', 'warning')
        return redirect(url_for('eventos'))
    
    try:
        # Obtener el evento
        evento = Evento.query.get_or_404(evento_id)
        
        # Verificar que el evento pertenezca a un animal de la finca
        animal = Animal.query.get(evento.animal_id)
        if not animal or animal.finca_id != session['finca_id']:
            flash('No tienes permiso para editar este evento', 'error')
            return redirect(url_for('eventos'))
        
        if request.method == 'POST':
            # Actualizar datos del evento
            evento.tipo_evento = request.form.get('tipo_evento')
            evento.fecha_evento = datetime.strptime(request.form.get('fecha_evento'), '%Y-%m-%d').date()
            evento.descripcion = request.form.get('descripcion')
            evento.responsable = request.form.get('responsable')
            
            # Campos específicos según tipo de evento
            if evento.tipo_evento == 'vendido':
                evento.comprador = request.form.get('comprador')
                evento.precio_venta = float(request.form.get('precio_venta')) if request.form.get('precio_venta') else None
            elif evento.tipo_evento == 'fallecido':
                evento.causa_muerte = request.form.get('causa_muerte')
            elif evento.tipo_evento == 'transferido':
                evento.descripcion = request.form.get('descripcion_transferencia')
            
            db.session.commit()
            flash('Evento actualizado exitosamente', 'success')
            return redirect(url_for('ver_evento', evento_id=evento.id))
        
        # Obtener lista de animales para el formulario
        animales = Animal.query.filter_by(finca_id=session['finca_id']).filter(Animal.estado.in_(['activo'])).all()
        
        return render_template('editar_evento.html', evento=evento, animal=animal, animales=animales)
        
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar el evento', 'error')
        print(f"Error al editar evento: {e}")
        return redirect(url_for('eventos'))

@app.route('/ajustes')
@login_required
def ajustes():
    """Página de ajustes del sistema"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar', 'warning')
        return redirect(url_for('fincas'))
    
    try:
        # Obtener información de la finca actual
        finca = Finca.query.get(session['finca_id'])
        if not finca:
            flash('Finca no encontrada', 'error')
            return redirect(url_for('fincas'))
        
        # Obtener estadísticas para mostrar
        animales_count = Animal.query.filter_by(finca_id=finca.id).count()
        
        eventos_count = Evento.query.join(Animal).filter(Animal.finca_id == finca.id).count()
        salud_count = EventoSalud.query.join(Animal).filter(Animal.finca_id == finca.id).count()
        vacunas_count = Vacuna.query.join(Animal).filter(Animal.finca_id == finca.id).count()
        
        return render_template('ajustes.html', 
                           finca=finca,
                           animales_count=animales_count,
                           eventos_count=eventos_count,
                           salud_count=salud_count,
                           vacunas_count=vacunas_count)
        
    except Exception as e:
        flash('Error al cargar ajustes', 'error')
        print(f"Error en ajustes: {e}")
        return redirect(url_for('index'))

@app.route('/descargar_respaldo_finca')
@login_required
def descargar_respaldo_finca():
    """Genera y descarga un respaldo de la base de datos de la finca seleccionada"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar', 'warning')
        return redirect(url_for('fincas'))
    
    try:
        # Obtener información de la finca
        finca = Finca.query.get(session['finca_id'])
        if not finca:
            flash('Finca no encontrada', 'error')
            return redirect(url_for('ajustes'))
        
        # Crear un respaldo JSON de todos los datos relacionados con la finca
        respaldo = {
            'informacion_finca': {
                'id': finca.id,
                'nombre': finca.nombre,
                'ubicacion': finca.ubicacion,
                'telefono': finca.telefono,
                'email': finca.email,
                'fecha_creacion': finca.fecha_fundacion.strftime('%Y-%m-%d') if finca.fecha_fundacion else None,
                'fecha_respaldo': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'animales': [],
            'eventos': [],
            'eventos_salud': [],
            'vacunas': [],
            'produccion': [],
            'potreros': [],
            'alimentacion': [],
            'inventario': []
        }
        
        # Exportar animales
        animales = Animal.query.filter_by(finca_id=finca.id).filter(Animal.estado.in_(['activo'])).all()
        for animal in animales:
            respaldo['animales'].append({
                'id': animal.id,
                'identificacion': animal.identificacion,
                'nombre': animal.nombre,
                'tipo': animal.tipo,
                'raza': animal.raza,
                'sexo': animal.sexo,
                'fecha_nacimiento': animal.fecha_nacimiento.strftime('%Y-%m-%d') if animal.fecha_nacimiento else None,
                'peso': float(animal.peso) if animal.peso else None,
                'estado': animal.estado,
                'imagen': animal.imagen
            })
        
        # Exportar eventos
        eventos = Evento.query.join(Animal).filter(Animal.finca_id == finca.id).all()
        for evento in eventos:
            respaldo['eventos'].append({
                'id': evento.id,
                'animal_id': evento.animal_id,
                'tipo_evento': evento.tipo_evento,
                'fecha_evento': evento.fecha_evento.strftime('%Y-%m-%d') if evento.fecha_evento else None,
                'descripcion': evento.descripcion,
                'responsable': evento.responsable,
                'comprador': getattr(evento, 'comprador', None),
                'precio_venta': float(getattr(evento, 'precio_venta', 0)) if getattr(evento, 'precio_venta', None) else None,
                'causa_muerte': getattr(evento, 'causa_muerte', None),
                'fecha_registro': evento.fecha_registro.strftime('%Y-%m-%d %H:%M:%S') if evento.fecha_registro else None
            })
        
        # Exportar eventos de salud
        eventos_salud = EventoSalud.query.join(Animal).filter(Animal.finca_id == finca.id).all()
        for evento in eventos_salud:
            respaldo['eventos_salud'].append({
                'id': evento.id,
                'animal_id': evento.animal_id,
                'tipo_evento': evento.tipo_evento,
                'titulo': evento.titulo,
                'fecha_evento': evento.fecha_evento.strftime('%Y-%m-%d') if evento.fecha_evento else None,
                'descripcion': evento.descripcion,
                'tratamiento': evento.tratamiento,
                'estado': evento.estado,
                'veterinario': evento.veterinario,
                'fecha_registro': evento.fecha_registro.strftime('%Y-%m-%d %H:%M:%S') if evento.fecha_registro else None
            })
        
        # Exportar vacunas
        vacunas = Vacuna.query.join(Animal).filter(Animal.finca_id == finca.id).all()
        for vacuna in vacunas:
            respaldo['vacunas'].append({
                'id': vacuna.id,
                'animal_id': vacuna.animal_id,
                'tipo_vacuna': vacuna.tipo_vacuna,
                'fecha_aplicacion': vacuna.fecha_aplicacion.strftime('%Y-%m-%d') if vacuna.fecha_aplicacion else None,
                'fecha_proxima': vacuna.fecha_proxima.strftime('%Y-%m-%d') if vacuna.fecha_proxima else None,
                'aplicada_por': vacuna.aplicada_por,
                'numero_lote': vacuna.numero_lote,
                'observaciones': vacuna.observaciones
            })
        
        # Exportar producción
        produccion = Produccion.query.join(Animal).filter(Animal.finca_id == finca.id).all()
        for prod in produccion:
            respaldo['produccion'].append({
                'id': prod.id,
                'animal_id': prod.animal_id,
                'tipo_produccion': prod.tipo_produccion,
                'cantidad': float(prod.cantidad) if prod.cantidad else None,
                'unidad': prod.unidad,
                'calidad': prod.calidad,
                'fecha': prod.fecha.strftime('%Y-%m-%d') if prod.fecha else None
            })
        
        # Exportar potreros
        potreros = Potrero.query.filter_by(finca_id=finca.id).all()
        for potrero in potreros:
            respaldo['potreros'].append({
                'id': potrero.id,
                'nombre': potrero.nombre,
                'area': float(potrero.area) if potrero.area else None,
                'capacidad': potrero.capacidad,
                'tipo_pasto': potrero.tipo_pasto,
                'estado': potrero.estado,
                'funcion': potrero.funcion
            })
        
        # Exportar alimentación
        alimentacion = HistorialAlimentacion.query.join(Animal).filter(Animal.finca_id == finca.id).all()
        for alim in alimentacion:
            respaldo['alimentacion'].append({
                'id': alim.id,
                'animal_id': alim.animal_id,
                'tipo_alimento': alim.tipo_alimento,
                'cantidad': float(alim.cantidad) if alim.cantidad else None,
                'unidad': getattr(alim, 'unidad', None),
                'fecha_alimentacion': alim.fecha_inicio.strftime('%Y-%m-%d %H:%M:%S') if alim.fecha_inicio else None
            })
        
        # Exportar inventario
        inventario = Inventario.query.filter_by(finca_id=finca.id).all()
        for item in inventario:
            respaldo['inventario'].append({
                'id': item.id,
                'producto': item.producto,
                'cantidad': float(item.cantidad) if item.cantidad else None,
                'unidad': item.unidad,
                'precio_unitario': float(item.precio_unitario) if item.precio_unitario else None,
                'fecha_vencimiento': item.fecha_vencimiento.strftime('%Y-%m-%d') if item.fecha_vencimiento else None,
                'categoria': item.categoria,
                'tipo_animal': item.tipo_animal
            })
        
        # Crear el archivo JSON
        import json
        json_data = json.dumps(respaldo, indent=2, ensure_ascii=False)
        
        # Crear respuesta para descarga
        from flask import Response
        response = Response(
            json_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=respaldo_finca_{finca.nombre}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )
        
        flash('Respaldo descargado exitosamente', 'success')
        return response
        
    except Exception as e:
        flash('Error al generar respaldo', 'error')
        print(f"Error al descargar respaldo: {e}")
        return redirect(url_for('ajustes'))

@app.route('/importar_respaldo_finca', methods=['GET', 'POST'])
@login_required
def importar_respaldo_finca():
    """Importa un respaldo de la base de datos de la finca"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar', 'warning')
        return redirect(url_for('fincas'))
    
    if request.method == 'GET':
        return render_template('importar_respaldo.html')
    
    try:
        if 'archivo_respaldo' not in request.files:
            flash('Por favor, selecciona un archivo JSON', 'error')
            return redirect(url_for('ajustes'))
        
        file = request.files['archivo_respaldo']
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('ajustes'))
        
        if not file.filename.endswith('.json'):
            flash('El archivo debe ser formato JSON', 'error')
            return redirect(url_for('ajustes'))
        
        # Leer el archivo JSON
        import json
        respaldo_data = json.loads(file.read().decode('utf-8'))
        
        # Validar estructura básica del JSON
        if 'informacion_finca' not in respaldo_data:
            flash('El archivo no parece ser un respaldo válido', 'error')
            return redirect(url_for('ajustes'))
        
        # Obtener finca actual
        finca = Finca.query.get(session['finca_id'])
        if not finca:
            flash('Finca no encontrada', 'error')
            return redirect(url_for('ajustes'))
        
        # Contador de registros importados
        registros_importados = {
            'animales': 0,
            'eventos': 0,
            'eventos_salud': 0,
            'vacunas': 0,
            'produccion': 0,
            'potreros': 0,
            'alimentacion': 0,
            'inventario': 0,
            'errores': []
        }
        
        # Importar animales
        if 'animales' in respaldo_data:
            for animal_data in respaldo_data['animales']:
                try:
                    # Verificar si el animal ya existe
                    animal_existente = Animal.query.filter_by(
                        finca_id=finca.id, 
                        identificacion=animal_data.get('identificacion')
                    ).first()
                    
                    if not animal_existente:
                        nuevo_animal = Animal(
                            finca_id=finca.id,
                            identificacion=animal_data.get('identificacion'),
                            nombre=animal_data.get('nombre'),
                            tipo=animal_data.get('tipo'),
                            raza=animal_data.get('raza'),
                            sexo=animal_data.get('sexo'),
                            peso=animal_data.get('peso'),
                            estado=animal_data.get('estado', 'activo'),
                            imagen=animal_data.get('imagen')
                        )
                        
                        if animal_data.get('fecha_nacimiento'):
                            nuevo_animal.fecha_nacimiento = datetime.strptime(animal_data['fecha_nacimiento'], '%Y-%m-%d').date()
                        
                        db.session.add(nuevo_animal)
                        registros_importados['animales'] += 1
                    else:
                        registros_importados['errores'].append(f"Animal {animal_data.get('identificacion')} ya existe")
                        
                except Exception as e:
                    registros_importados['errores'].append(f"Error importando animal {animal_data.get('identificacion')}: {str(e)}")
        
        # Importar eventos
        if 'eventos' in respaldo_data:
            for evento_data in respaldo_data['eventos']:
                try:
                    # Verificar que el animal existe
                    animal = Animal.query.filter_by(
                        finca_id=finca.id,
                        identificacion=evento_data.get('animal_id')
                    ).first()
                    
                    if animal:
                        nuevo_evento = Evento(
                            animal_id=animal.id,
                            tipo_evento=evento_data.get('tipo_evento'),
                            descripcion=evento_data.get('descripcion'),
                            responsable=evento_data.get('responsable')
                        )
                        
                        if evento_data.get('fecha_evento'):
                            nuevo_evento.fecha_evento = datetime.strptime(evento_data['fecha_evento'], '%Y-%m-%d').date()
                        
                        # Campos específicos según tipo
                        if evento_data.get('tipo_evento') == 'vendido':
                            nuevo_evento.comprador = evento_data.get('comprador')
                            nuevo_evento.precio_venta = evento_data.get('precio_venta')
                        elif evento_data.get('tipo_evento') == 'fallecido':
                            nuevo_evento.causa_muerte = evento_data.get('causa_muerte')
                        
                        db.session.add(nuevo_evento)
                        registros_importados['eventos'] += 1
                    else:
                        registros_importados['errores'].append(f"Animal no encontrado para evento ID {evento_data.get('animal_id')}")
                        
                except Exception as e:
                    registros_importados['errores'].append(f"Error importando evento: {str(e)}")
        
        # Importar eventos de salud
        if 'eventos_salud' in respaldo_data:
            for evento_data in respaldo_data['eventos_salud']:
                try:
                    animal = Animal.query.filter_by(
                        finca_id=finca.id,
                        identificacion=evento_data.get('animal_id')
                    ).first()
                    
                    if animal:
                        nuevo_evento = EventoSalud(
                            animal_id=animal.id,
                            tipo_evento=evento_data.get('tipo_evento'),
                            titulo=evento_data.get('titulo'),
                            descripcion=evento_data.get('descripcion'),
                            tratamiento=evento_data.get('tratamiento'),
                            estado=evento_data.get('estado'),
                            veterinario=evento_data.get('veterinario')
                        )
                        
                        if evento_data.get('fecha_evento'):
                            nuevo_evento.fecha_evento = datetime.strptime(evento_data['fecha_evento'], '%Y-%m-%d').date()
                        
                        db.session.add(nuevo_evento)
                        registros_importados['eventos_salud'] += 1
                    else:
                        registros_importados['errores'].append(f"Animal no encontrado para evento de salud ID {evento_data.get('animal_id')}")
                        
                except Exception as e:
                    registros_importados['errores'].append(f"Error importando evento de salud: {str(e)}")
        
        # Importar vacunas
        if 'vacunas' in respaldo_data:
            for vacuna_data in respaldo_data['vacunas']:
                try:
                    animal = Animal.query.filter_by(
                        finca_id=finca.id,
                        identificacion=vacuna_data.get('animal_id')
                    ).first()
                    
                    if animal:
                        nueva_vacuna = Vacuna(
                            animal_id=animal.id,
                            tipo_vacuna=vacuna_data.get('tipo_vacuna'),
                            aplicada_por=vacuna_data.get('aplicada_por'),
                            numero_lote=vacuna_data.get('numero_lote'),
                            observaciones=vacuna_data.get('observaciones')
                        )
                        
                        if vacuna_data.get('fecha_aplicacion'):
                            nueva_vacuna.fecha_aplicacion = datetime.strptime(vacuna_data['fecha_aplicacion'], '%Y-%m-%d').date()
                        if vacuna_data.get('fecha_proxima'):
                            nueva_vacuna.fecha_proxima = datetime.strptime(vacuna_data['fecha_proxima'], '%Y-%m-%d').date()
                        
                        db.session.add(nueva_vacuna)
                        registros_importados['vacunas'] += 1
                    else:
                        registros_importados['errores'].append(f"Animal no encontrado para vacuna ID {vacuna_data.get('animal_id')}")
                        
                except Exception as e:
                    registros_importados['errores'].append(f"Error importando vacuna: {str(e)}")
        
        # Confirmar todos los cambios
        db.session.commit()
        
        # Mensaje de éxito
        mensaje_exito = f"""
        Importación completada:
        ✅ Animales: {registros_importados['animales']}
        ✅ Eventos: {registros_importados['eventos']}
        ✅ Eventos de salud: {registros_importados['eventos_salud']}
        ✅ Vacunas: {registros_importados['vacunas']}
        """
        
        if registros_importados['errores']:
            mensaje_exito += f"\n⚠️ Errores: {len(registros_importados['errores'])}"
            for error in registros_importados['errores'][:5]:  # Mostrar solo primeros 5 errores
                mensaje_exito += f"\n• {error}"
        
        flash(mensaje_exito, 'success')
        return redirect(url_for('ajustes'))
        
    except json.JSONDecodeError:
        flash('El archivo JSON no es válido', 'error')
        return redirect(url_for('ajustes'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al importar respaldo: {str(e)}', 'error')
        print(f"Error al importar respaldo: {e}")
        return redirect(url_for('ajustes'))

@app.route('/reporte_finca_completo_pdf')
@login_required
def reporte_finca_completo_pdf():
    """Genera un reporte PDF completo de toda la finca"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        import io
        from datetime import datetime
        
        # Configuración del PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Obtener datos de la finca
        finca = Finca.query.get(session['finca_id'])
        if not finca:
            flash('Finca no encontrada', 'error')
            return redirect(url_for('ajustes'))
        
        # Contenido del PDF
        story = []
        
        # Título principal
        story.append(Paragraph(f"REPORTE COMPLETO DE LA FINCA", title_style))
        story.append(Paragraph(f"{finca.nombre}", styles['Heading2']))
        story.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # 1. Información de la Finca
        story.append(Paragraph("1. INFORMACIÓN GENERAL", heading_style))
        
        info_data = [
            ['Nombre:', finca.nombre or 'N/A'],
            ['Ubicación:', finca.ubicacion or 'N/A'],
            ['Teléfono:', finca.telefono or 'N/A'],
            ['Email:', finca.email or 'N/A'],
            ['Fecha Fundación:', finca.fecha_fundacion.strftime('%d/%m/%Y') if finca.fecha_fundacion else 'N/A']
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # 2. Animales
        story.append(PageBreak())
        story.append(Paragraph("2. ANIMALES", heading_style))
        
        animales = Animal.query.filter_by(finca_id=finca.id).filter(Animal.estado.in_(['activo'])).all()
        if animales:
            animales_data = [['ID', 'Identificación', 'Nombre', 'Raza', 'Tipo', 'Sexo', 'Estado']]
            for animal in animales:
                animales_data.append([
                    str(animal.id),
                    animal.identificacion or 'N/A',
                    animal.nombre or 'N/A',
                    animal.raza or 'N/A',
                    animal.tipo or 'N/A',
                    animal.sexo or 'N/A',
                    animal.estado or 'N/A'
                ])
            
            animales_table = Table(animales_data, colWidths=[0.5*inch, 1*inch, 1.2*inch, 1*inch, 1*inch, 0.8*inch, 1*inch])
            animales_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            story.append(animales_table)
            story.append(Paragraph(f"Total animales: {len(animales)}", styles['Normal']))
        else:
            story.append(Paragraph("No hay animales registrados", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # 3. Producción
        story.append(Paragraph("3. PRODUCCIÓN", heading_style))
        
        producciones = Produccion.query.filter_by(finca_id=finca.id).all()
        if producciones:
            prod_data = [['Fecha', 'Animal', 'Tipo', 'Cantidad', 'Unidad']]
            for prod in producciones:
                prod_data.append([
                    prod.fecha.strftime('%d/%m/%Y') if prod.fecha else 'N/A',
                    prod.animal.nombre if prod.animal else 'N/A',
                    prod.tipo_produccion or 'N/A',
                    str(prod.cantidad) if prod.cantidad else '0',
                    prod.unidad or 'N/A'
                ])
            
            prod_table = Table(prod_data, colWidths=[1*inch, 1.5*inch, 1.2*inch, 0.8*inch, 0.8*inch])
            prod_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            story.append(prod_table)
            story.append(Paragraph(f"Total registros: {len(producciones)}", styles['Normal']))
        else:
            story.append(Paragraph("No hay registros de producción", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # 4. Salud y Vacunas
        story.append(PageBreak())
        story.append(Paragraph("4. SALUD Y VACUNAS", heading_style))
        
        # Eventos de salud
        eventos_salud = EventoSalud.query.join(Animal).filter(Animal.finca_id == finca.id).all()
        if eventos_salud:
            salud_data = [['Fecha', 'Animal', 'Tipo', 'Descripción']]
            for evento in eventos_salud:
                salud_data.append([
                    evento.fecha_evento.strftime('%d/%m/%Y') if evento.fecha_evento else 'N/A',
                    evento.animal.nombre if evento.animal else 'N/A',
                    evento.tipo_evento or 'N/A',
                    (evento.descripcion or '')[:30] + '...' if len(evento.descripcion or '') > 30 else (evento.descripcion or 'N/A')
                ])
            
            salud_table = Table(salud_data, colWidths=[1*inch, 1.5*inch, 1.2*inch, 2*inch])
            salud_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            story.append(salud_table)
            story.append(Paragraph(f"Total eventos de salud: {len(eventos_salud)}", styles['Normal']))
        else:
            story.append(Paragraph("No hay eventos de salud registrados", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Vacunas
        vacunas = Vacuna.query.join(Animal).filter(Animal.finca_id == finca.id).all()
        if vacunas:
            vac_data = [['Fecha', 'Animal', 'Vacuna', 'Próxima Dosis']]
            for vac in vacunas:
                vac_data.append([
                    vac.fecha_aplicacion.strftime('%d/%m/%Y') if vac.fecha_aplicacion else 'N/A',
                    vac.animal.nombre if vac.animal else 'N/A',
                    vac.tipo_vacuna or 'N/A',
                    vac.fecha_proxima.strftime('%d/%m/%Y') if vac.fecha_proxima else 'N/A'
                ])
            
            vac_table = Table(vac_data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 1*inch])
            vac_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkorange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            story.append(vac_table)
            story.append(Paragraph(f"Total vacunas aplicadas: {len(vacunas)}", styles['Normal']))
        else:
            story.append(Paragraph("No hay vacunas registradas", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # 5. Inventario
        story.append(Paragraph("5. INVENTARIO", heading_style))
        
        inventario = Inventario.query.filter_by(finca_id=finca.id).all()
        if inventario:
            inv_data = [['Producto', 'Cantidad', 'Unidad', 'Precio Unitario', 'Valor Total']]
            total_valor = 0
            for item in inventario:
                valor_total = (item.cantidad or 0) * (item.precio_unitario or 0)
                total_valor += valor_total
                inv_data.append([
                    item.producto or 'N/A',
                    str(item.cantidad) if item.cantidad else '0',
                    item.unidad or 'N/A',
                    f"${item.precio_unitario:.2f}" if item.precio_unitario else '$0.00',
                    f"${valor_total:.2f}"
                ])
            
            inv_table = Table(inv_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch])
            inv_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            story.append(inv_table)
            story.append(Paragraph(f"Valor total del inventario: ${total_valor:.2f}", styles['Normal']))
        else:
            story.append(Paragraph("No hay items en el inventario", styles['Normal']))
        
        # Generar PDF
        doc.build(story)
        buffer.seek(0)
        
        # Preparar respuesta
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=reporte_completo_{finca.nombre}_{datetime.now().strftime("%Y%m%d")}.pdf'
        
        buffer.close()
        return response
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generando reporte PDF completo: {error_details}")
        flash(f'Error al generar el reporte PDF: {str(e)}', 'error')
        return redirect(url_for('ajustes'))

# Rutas para Inventario
@app.route('/inventario')
@login_required
def inventario():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    inventarios = Inventario.query.filter_by(finca_id=session['finca_id']).order_by(Inventario.fecha_vencimiento.asc()).all()
    
    total_valor_inventario = db.session.query(db.func.sum(Inventario.cantidad * Inventario.precio_unitario)).filter_by(finca_id=session['finca_id']).scalar() or 0
    
    productos_vencidos_count = 0
    productos_por_vencer_count = 0
    productos_por_vencer_list = []
    
    today = date.today()
    
    for item in inventarios:
        if item.fecha_vencimiento:
            dias_restantes = (item.fecha_vencimiento - today).days
            if dias_restantes < 0:
                productos_vencidos_count += 1
            elif dias_restantes <= 30:
                productos_por_vencer_count += 1
                productos_por_vencer_list.append(item)
    
    return render_template('inventario.html', 
                           inventarios=inventarios, 
                           total_valor_inventario=total_valor_inventario,
                           productos_vencidos_count=productos_vencidos_count,
                           productos_por_vencer_count=productos_por_vencer_count,
                           productos_por_vencer_list=productos_por_vencer_list,
                           today=datetime.utcnow().date())

@app.route('/reporte_inventario_pdf')
@login_required
def reporte_inventario_pdf():
    """Genera un reporte PDF del inventario"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.lib import colors
        from io import BytesIO
        
        finca_id = session['finca_id']
        finca = Finca.query.get(finca_id)
        
        # Obtener datos del inventario
        inventarios = Inventario.query.filter_by(finca_id=finca_id).order_by(Inventario.categoria, Inventario.producto).all()
        
        # Calcular totales
        total_valor = sum(item.cantidad * item.precio_unitario for item in inventarios)
        total_productos = len(inventarios)
        
        # Contar por estado
        hoy = date.today()
        vencidos = 0
        por_vencer = 0
        vigentes = 0
        
        for item in inventarios:
            if item.fecha_vencimiento:
                dias = (item.fecha_vencimiento - hoy).days
                if dias < 0:
                    vencidos += 1
                elif dias <= 30:
                    por_vencer += 1
                else:
                    vigentes += 1
            else:
                vigentes += 1
        
        # Crear PDF en orientación landscape para más espacio
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        
        # Colores
        color_primario = colors.HexColor('#1a365d')
        color_secundario = colors.HexColor('#4a5568')
        
        # Estilos
        titulo_style = ParagraphStyle(
            'Titulo',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            textColor=color_primario,
            fontName='Helvetica-Bold',
            spaceAfter=10
        )
        
        subtitulo_style = ParagraphStyle(
            'Subtitulo',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=color_secundario,
            spaceAfter=20
        )
        
        elements = []
        
        # Título
        elements.append(Paragraph("REPORTE DE INVENTARIO", titulo_style))
        
        # Info de finca
        finca_texto = finca.nombre.upper() if finca else "FINCA"
        elements.append(Paragraph(finca_texto, subtitulo_style))
        
        # Fecha
        fecha_actual = datetime.now()
        fecha_texto = "Generado el " + fecha_actual.strftime('%d/%m/%Y a las %H:%M')
        elements.append(Paragraph(fecha_texto, subtitulo_style))
        elements.append(Spacer(1, 15))
        
        # Tabla de resumen
        resumen_data = [
            ['TOTAL PRODUCTOS', 'VALOR TOTAL', 'VIGENTES', 'POR VENCER', 'VENCIDOS'],
            [str(total_productos), "${:,.2f}".format(total_valor), str(vigentes), str(por_vencer), str(vencidos)]
        ]
        
        resumen_table = Table(resumen_data, colWidths=[doc.width*0.18]*5)
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), color_primario),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, 1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f7fafc')),
        ]))
        elements.append(resumen_table)
        elements.append(Spacer(1, 25))
        
        # Tabla de inventario detallado
        data = [['PRODUCTO', 'CATEGORÍA', 'CANTIDAD', 'UNIDAD', 'PRECIO UNIT.', 'VALOR TOTAL', 'VENCIMIENTO', 'ESTADO']]
        
        for item in inventarios:
            valor_total = item.cantidad * item.precio_unitario
            
            # Determinar estado
            if item.fecha_vencimiento:
                dias = (item.fecha_vencimiento - hoy).days
                if dias < 0:
                    estado = 'VENCIDO'
                    color_estado = colors.HexColor('#e53e3e')
                elif dias <= 30:
                    estado = 'POR VENCER'
                    color_estado = colors.HexColor('#28a745')
                else:
                    estado = 'VIGENTE'
                    color_estado = colors.HexColor('#28a745')
            else:
                estado = 'VIGENTE'
                color_estado = colors.HexColor('#28a745')
            
            vencimiento = item.fecha_vencimiento.strftime('%d/%m/%Y') if item.fecha_vencimiento else 'N/A'
            
            data.append([
                item.producto,
                item.categoria.title(),
                "{:.2f}".format(item.cantidad),
                item.unidad,
                "${:,.2f}".format(item.precio_unitario),
                "${:,.2f}".format(valor_total),
                vencimiento,
                estado
            ])
        
        # Crear tabla
        col_widths = [
            doc.width*0.20,  # Producto
            doc.width*0.12,  # Categoría
            doc.width*0.08,  # Cantidad
            doc.width*0.08,  # Unidad
            doc.width*0.12,  # Precio Unit.
            doc.width*0.12,  # Valor Total
            doc.width*0.10,  # Vencimiento
            doc.width*0.10,  # Estado
        ]
        
        tabla = Table(data, colWidths=col_widths, repeatRows=1)
        tabla.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), color_primario),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            
            # Datos
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),  # Cantidad
            ('ALIGN', (4, 1), (5, -1), 'RIGHT'),  # Precios
            ('ALIGN', (6, 1), (7, -1), 'CENTER'),  # Vencimiento y Estado
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, color_primario),
            
            # Alternar colores de fila
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        # Colorear estados
        for i, item in enumerate(inventarios, start=1):
            if item.fecha_vencimiento:
                dias = (item.fecha_vencimiento - hoy).days
                if dias < 0:
                    bg_color = colors.HexColor('#fed7d7')  # Rojo claro
                elif dias <= 30:
                    bg_color = colors.HexColor('#feebc8')  # Naranja claro
                else:
                    bg_color = colors.HexColor('#c6f6d5')  # Verde claro
            else:
                bg_color = colors.HexColor('#c6f6d5')  # Verde claro
            
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, i), (-1, i), bg_color),
            ]))
        
        elements.append(tabla)
        elements.append(Spacer(1, 20))
        
        # Pie de página
        pie_texto = (finca.nombre if finca else 'Empresa') + " - Sistema de Gestión Agropecuaria"
        pie_style = ParagraphStyle(
            'Pie',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#a0aec0')
        )
        elements.append(Paragraph(pie_texto, pie_style))
        
        # Generar PDF
        doc.build(elements)
        
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name='Reporte_Inventario_' + (finca.nombre if finca else 'Finca').replace(' ', '_') + '_' + fecha_actual.strftime('%Y%m%d') + '.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        import traceback
        print("[ERROR] Error al generar reporte de inventario: " + str(e))
        print("[ERROR] Traceback: " + traceback.format_exc())
        flash('Error al generar el reporte: ' + str(e), 'danger')
        return redirect(url_for('inventario'))

@app.route('/inventario/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_inventario():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    if request.method == 'POST':
        categoria = request.form['categoria']
        unidad = request.form['unidad']
        tipo_animal = request.form['tipo_animal']
        if request.form.get('otra_categoria'):
            categoria = request.form['otra_categoria']
        if request.form.get('otra_unidad'):
            unidad = request.form['otra_unidad']
        fecha_vencimiento = None
        if request.form.get('fecha_vencimiento'):
            fecha_vencimiento = datetime.strptime(request.form['fecha_vencimiento'], '%Y-%m-%d').date()
        inventario = Inventario(
            producto=request.form['producto'],
            cantidad=float(request.form['cantidad']),
            unidad=unidad,
            precio_unitario=float(request.form['precio_unitario']),
            fecha_vencimiento=fecha_vencimiento,
            categoria=categoria,
            tipo_animal=tipo_animal,
            finca_id=session['finca_id']
        )
        db.session.add(inventario)
        db.session.commit()
        # Registrar movimiento de entrada
        movimiento = MovimientoInventario(
            inventario_id=inventario.id,
            tipo_movimiento='entrada',
            cantidad=inventario.cantidad,
            motivo='Registro inicial'
        )
        db.session.add(movimiento)
        db.session.commit()
        # Registrar entrega a animal si se selecciona
        animal_id = request.form.get('animal_id')
        cantidad_entregada = request.form.get('cantidad_entregada')
        if animal_id and cantidad_entregada:
            movimiento_animal = MovimientoInventarioAnimal(
                inventario_id=inventario.id,
                animal_id=int(animal_id),
                cantidad=float(cantidad_entregada),
                motivo='Entrega inicial',
                observaciones=request.form.get('observaciones_entrega')
            )
            db.session.add(movimiento_animal)
            db.session.commit()
        flash('Producto agregado al inventario exitosamente')
        return redirect(url_for('inventario'))
    tipos_animales = db.session.query(Animal.tipo).filter_by(finca_id=session['finca_id']).distinct().all()
    tipos_animales = [t[0] for t in tipos_animales]
    animales = Animal.query.filter_by(finca_id=session['finca_id']).filter(Animal.estado.in_(['activo'])).all()
    return render_template('nuevo_inventario.html', tipos_animales=tipos_animales, animales=animales, inventario=None, editar=False)

@app.route('/inventario/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_inventario(id):
    inventario = Inventario.query.get_or_404(id)
    if inventario.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('inventario'))
    if request.method == 'POST':
        inventario.producto = request.form['producto']
        inventario.cantidad = float(request.form['cantidad'])
        inventario.unidad = request.form['unidad']
        inventario.precio_unitario = float(request.form['precio_unitario'])
        inventario.categoria = request.form['categoria']
        inventario.tipo_animal = request.form.get('tipo_animal')
        fecha_vencimiento = request.form.get('fecha_vencimiento')
        inventario.fecha_vencimiento = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date() if fecha_vencimiento else None
        db.session.commit()
        flash('Producto actualizado exitosamente', 'success')
        return redirect(url_for('inventario'))
    return render_template('nuevo_inventario.html', inventario=inventario, editar=True)

@app.route('/inventario/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_inventario(id):
    inventario = Inventario.query.get_or_404(id)
    if inventario.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('inventario'))
    db.session.delete(inventario)
    db.session.commit()
    flash('Producto eliminado exitosamente', 'success')
    return redirect(url_for('inventario'))

@app.route('/animal/<int:animal_id>/notas', methods=['GET', 'POST'])
@login_required
def notas_animal(animal_id):
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    animal = Animal.query.get_or_404(animal_id)
    if request.method == 'POST':
        nota = NotaAnimal(
            animal_id=animal_id,
            nota=request.form['nota']
        )
        db.session.add(nota)
        db.session.commit()
        flash('Nota agregada exitosamente')
        return redirect(url_for('notas_animal', animal_id=animal_id))
    # Corregido: NotaAnimal no tiene campo finca_id, filtramos solo por animal_id
    notas = NotaAnimal.query.filter_by(animal_id=animal_id).order_by(NotaAnimal.fecha.desc()).all()
    return render_template('notas_animal.html', animal=animal, notas=notas)

# Rutas para el historial completo de animales
@app.route('/animal/<int:animal_id>/historial')
@login_required
def historial_animal(animal_id):
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    animal = Animal.query.get_or_404(animal_id)
    if animal.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('animales'))
    
    # Obtener información del potrero actual del animal
    potrero_actual = None
    if animal.potrero_id:
        potrero_actual = Potrero.query.get(animal.potrero_id)
    
    historial_alimentacion = HistorialAlimentacion.query.filter_by(animal_id=animal_id).order_by(HistorialAlimentacion.fecha_inicio.desc()).all()
    historial_salud = HistorialSalud.query.filter_by(animal_id=animal_id).filter(~HistorialSalud.tipo_evento.like('%vacun%')).order_by(HistorialSalud.fecha_inicio.desc()).all()
    eventos_salud = EventoSalud.query.filter_by(animal_id=animal_id).order_by(EventoSalud.fecha_evento.desc()).all()
    vacunas = Vacuna.query.filter_by(animal_id=animal_id).order_by(Vacuna.fecha_aplicacion.desc()).all()
    servicios = ServicioReproductivo.query.filter_by(animal_id=animal_id).order_by(ServicioReproductivo.fecha.desc()).all()
    preneces = DiagnosticoPrenez.query.filter_by(animal_id=animal_id).order_by(DiagnosticoPrenez.fecha.desc()).all()
    partos = Parto.query.filter_by(animal_id=animal_id).order_by(Parto.fecha.desc()).all()
    producciones = Produccion.query.filter_by(animal_id=animal_id).order_by(Produccion.fecha.desc()).all()
    notas = NotaAnimal.query.filter_by(animal_id=animal_id).order_by(NotaAnimal.fecha.desc()).all()
    entregas_inventario = MovimientoInventarioAnimal.query.filter_by(animal_id=animal_id).order_by(MovimientoInventarioAnimal.fecha.desc()).all()
    eventos = Evento.query.filter_by(animal_id=animal_id).order_by(Evento.fecha_evento.desc()).all()
    
    return render_template('historial_animal.html', 
                         animal=animal,
                         potrero_actual=potrero_actual,
                         historial_alimentacion=historial_alimentacion,
                         historial_salud=historial_salud,
                         eventos_salud=eventos_salud,
                         vacunas=vacunas,
                         producciones=producciones,
                         notas=notas,
                         entregas_inventario=entregas_inventario,
                         eventos=eventos,
                         servicios=servicios,
                         preneces=preneces,
                         partos=partos,
                         today=datetime.utcnow().date())

@app.route('/animal/<int:animal_id>/historial/pdf')
@login_required
def imprimir_historial_pdf(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    if animal.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('animales'))
    
    if not WEASYPRINT_AVAILABLE:
        flash('WeasyPrint no está instalado en el servidor. Exportación limitada.', 'warning')
        return redirect(url_for('historial_animal', animal_id=animal_id))

    historial_alimentacion = HistorialAlimentacion.query.filter_by(animal_id=animal_id).order_by(HistorialAlimentacion.fecha_inicio.desc()).all()
    historial_salud = HistorialSalud.query.filter_by(animal_id=animal_id).filter(~HistorialSalud.tipo_evento.like('%vacun%')).order_by(HistorialSalud.fecha_inicio.desc()).all()
    eventos_salud = EventoSalud.query.filter_by(animal_id=animal_id).order_by(EventoSalud.fecha_evento.desc()).all()
    vacunas = Vacuna.query.filter_by(animal_id=animal_id).order_by(Vacuna.fecha_aplicacion.desc()).all()
    producciones = Produccion.query.filter_by(animal_id=animal_id).order_by(Produccion.fecha.desc()).all()
    notas = NotaAnimal.query.filter_by(animal_id=animal_id).order_by(NotaAnimal.fecha.desc()).all()

    html = render_template('historial_animal.html', animal=animal, historial_alimentacion=historial_alimentacion, historial_salud=historial_salud, eventos_salud=eventos_salud, vacunas=vacunas, producciones=producciones, notas=notas, pdf=True)
    pdf_file = HTML(string=html, base_url=request.base_url).write_pdf()
    response = make_response(pdf_file)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=historial_{animal.identificacion}.pdf'
    return response

@app.route('/animal/<int:animal_id>/certificado')
@login_required
def certificado_animal(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    if animal.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('animales'))
    if not WEASYPRINT_AVAILABLE:
        flash('WeasyPrint no está instalado en el servidor.', 'warning')
        return redirect(url_for('historial_animal', animal_id=animal_id))
    # Generar un certificado breve con QR
    verification_url = url_for('verificar_certificado', animal_id=animal.id, _external=True)
    html = render_template('certificado_animal.html', animal=animal, verification_url=verification_url, date=date)
    pdf_file = HTML(string=html, base_url=request.base_url).write_pdf()
    response = make_response(pdf_file)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=certificado_{animal.identificacion}.pdf'
    return response

@app.route('/verificar_certificado/<int:animal_id>')
def verificar_certificado(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    return render_template('verificar_certificado.html', animal=animal, date=date)

@app.route('/animal/<int:animal_id>/qr')
@login_required
def generar_qr_animal(animal_id):
    """Genera un código QR para un animal que apunta a sus detalles"""
    if not QR_AVAILABLE:
        flash('La funcionalidad de códigos QR no está disponible.', 'warning')
        return redirect(url_for('animales'))
    
    animal = Animal.query.get_or_404(animal_id)
    if animal.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('animales'))
    
    # Generar URL para los detalles del animal con IP local
    import socket
    try:
        # Obtener la IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.254.254.254', 1))
        local_ip = s.getsockname()[0]
        s.close()
        detalles_url = f"http://{local_ip}:5000/animal/qr/{animal.id}"
    except:
        # Si no se puede obtener la IP, usar la URL por defecto
        detalles_url = url_for('verificar_animal_qr', animal_id=animal.id, _external=True)
    
    # Crear QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(detalles_url)
    qr.make(fit=True)
    
    # Generar imagen
    img = qr.make_image(fill_color="#007bff", back_color="white")
    
    # Convertir a bytes para enviar como respuesta
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    response = make_response(img_buffer.getvalue())
    response.headers['Content-Type'] = 'image/png'
    response.headers['Content-Disposition'] = f'inline; filename=qr_{animal.identificacion}.png'
    
    return response

@app.route('/animal/qr/<int:animal_id>')
def verificar_animal_qr(animal_id):
    """Endpoint público para ver detalles de un animal al escanear su QR"""
    from datetime import datetime
    animal = Animal.query.get_or_404(animal_id)
    
    # Obtener información adicional del animal
    potrero = None
    if animal.potrero_id:
        potrero = Potrero.query.get(animal.potrero_id)
    
    # Obtener las vacunas del animal
    vacunas = Vacuna.query.filter_by(animal_id=animal_id).order_by(Vacuna.fecha_aplicacion.desc()).all()
    
    return render_template('animal_qr_detalles.html', animal=animal, potrero=potrero, vacunas=vacunas, date=datetime.now())

@app.route('/animal/<int:animal_id>/alimentacion/nueva', methods=['GET', 'POST'])
@login_required
def nueva_alimentacion(animal_id):
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    animal = Animal.query.get_or_404(animal_id)
    if animal.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('animales'))
    
    if request.method == 'POST':
        alimentacion = HistorialAlimentacion(
            animal_id=animal_id,
            tipo_alimento=request.form['tipo_alimento'],
            marca=request.form.get('marca'),
            composicion=request.form.get('composicion'),
            cantidad_diaria=float(request.form['cantidad_diaria']) if request.form.get('cantidad_diaria') else None,
            unidad=request.form.get('unidad'),
            fecha_inicio=datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d').date(),
            fecha_fin=datetime.strptime(request.form['fecha_fin'], '%Y-%m-%d').date() if request.form.get('fecha_fin') else None,
            observaciones=request.form.get('observaciones')
        )
        db.session.add(alimentacion)
        db.session.commit()
        flash('Registro de alimentación agregado exitosamente', 'success')
        return redirect(url_for('historial_animal', animal_id=animal_id))
    
    return render_template('nueva_alimentacion.html', animal=animal)

@app.route('/animal/<int:animal_id>/servicio/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_servicio_reproductivo(animal_id):
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    animal = Animal.query.get_or_404(animal_id)
    if animal.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('animales'))
    if request.method == 'POST':
        servicio = ServicioReproductivo(
            animal_id=animal_id,
            fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
            tipo_servicio=request.form['tipo_servicio'],
            semental_id=parse_int(request.form.get('semental_id')),
            semental_nombre=request.form.get('semental_nombre'),
            responsable=request.form.get('responsable'),
            observaciones=request.form.get('observaciones')
        )
        db.session.add(servicio)
        db.session.commit()
        flash('Servicio reproductivo registrado', 'success')
        return redirect(url_for('historial_animal', animal_id=animal_id))
    sementales = Animal.query.filter_by(finca_id=session['finca_id']).filter(Animal.estado.in_(['activo'])).all()
    return render_template('nuevo_servicio.html', animal=animal, sementales=sementales)

@app.route('/animal/<int:animal_id>/prenez/nueva', methods=['GET', 'POST'])
@login_required
def nuevo_diagnostico_prenez(animal_id):
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    animal = Animal.query.get_or_404(animal_id)
    if animal.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('animales'))
    if request.method == 'POST':
        diag = DiagnosticoPrenez(
            animal_id=animal_id,
            fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
            resultado=request.form['resultado'],
            metodo=request.form.get('metodo'),
            semanas_gestacion=parse_int(request.form.get('semanas_gestacion')),
            observaciones=request.form.get('observaciones')
        )
        db.session.add(diag)
        db.session.commit()
        flash('Diagnóstico de preñez registrado', 'success')
        return redirect(url_for('historial_animal', animal_id=animal_id))
    return render_template('nueva_prenez.html', animal=animal)

@app.route('/animal/<int:animal_id>/parto/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_parto(animal_id):
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    animal = Animal.query.get_or_404(animal_id)
    if animal.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('animales'))
    if request.method == 'POST':
        parto = Parto(
            animal_id=animal_id,
            fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
            crias_vivas=parse_int(request.form.get('crias_vivas')),
            crias_muertas=parse_int(request.form.get('crias_muertas')),
            peso_promedio_crias=float(request.form['peso_promedio_crias']) if request.form.get('peso_promedio_crias') else None,
            dificultades=request.form.get('dificultades'),
            observaciones=request.form.get('observaciones')
        )
        db.session.add(parto)
        # actualizar métricas básicas de la hembra
        animal.numero_partos = (animal.numero_partos or 0) + 1
        db.session.commit()
        flash('Parto registrado', 'success')
        return redirect(url_for('historial_animal', animal_id=animal_id))
    return render_template('nuevo_parto.html', animal=animal)

@app.route('/animal/<int:animal_id>/salud/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_evento_salud(animal_id):
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    animal = Animal.query.get_or_404(animal_id)
    if animal.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('animales'))
    
    if request.method == 'POST':
        evento_salud = HistorialSalud(
            animal_id=animal_id,
            tipo_evento=request.form['tipo_evento'],
            descripcion=request.form['descripcion'],
            fecha_inicio=datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d').date(),
            fecha_fin=datetime.strptime(request.form['fecha_fin'], '%Y-%m-%d').date() if request.form.get('fecha_fin') else None,
            tratamiento=request.form.get('tratamiento'),
            dias_tratamiento=int(request.form['dias_tratamiento']) if request.form.get('dias_tratamiento') else None,
            resultado=request.form.get('resultado'),
            observaciones=request.form.get('observaciones')
        )
        db.session.add(evento_salud)
        db.session.commit()
        flash('Evento de salud registrado exitosamente', 'success')
        return redirect(url_for('historial_animal', animal_id=animal_id))
    
    return render_template('nuevo_evento_salud.html', animal=animal)

@app.route('/animal/<int:animal_id>/reproductivo/actualizar', methods=['GET', 'POST'])
@login_required
def actualizar_reproductivo(animal_id):
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    animal = Animal.query.get_or_404(animal_id)
    if animal.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('animales'))
    
    if request.method == 'POST':
        # Actualizar información reproductiva según el sexo
        if animal.sexo == 'Hembra':
            animal.fecha_servicio = datetime.strptime(request.form['fecha_servicio'], '%Y-%m-%d').date() if request.form.get('fecha_servicio') else None
            animal.semental_utilizado = request.form.get('semental_utilizado')
            animal.fecha_estimada_parto = datetime.strptime(request.form['fecha_estimada_parto'], '%Y-%m-%d').date() if request.form.get('fecha_estimada_parto') else None
            animal.fecha_real_parto = datetime.strptime(request.form['fecha_real_parto'], '%Y-%m-%d').date() if request.form.get('fecha_real_parto') else None
            animal.lechones_nacidos_vivos = int(request.form['lechones_nacidos_vivos']) if request.form.get('lechones_nacidos_vivos') else None
            animal.lechones_nacidos_muertos = int(request.form['lechones_nacidos_muertos']) if request.form.get('lechones_nacidos_muertos') else None
            animal.peso_promedio_lechones = float(request.form['peso_promedio_lechones']) if request.form.get('peso_promedio_lechones') else None
            if request.form.get('fecha_real_parto'):
                animal.numero_partos = (animal.numero_partos or 0) + 1
        else:  # Macho
            animal.fecha_inicio_semental = datetime.strptime(request.form['fecha_inicio_semental'], '%Y-%m-%d').date() if request.form.get('fecha_inicio_semental') else None
            animal.numero_servicios_exitosos = int(request.form['numero_servicios_exitosos']) if request.form.get('numero_servicios_exitosos') else None
            animal.promedio_lechones_por_camada = float(request.form['promedio_lechones_por_camada']) if request.form.get('promedio_lechones_por_camada') else None
        
        db.session.commit()
        flash('Información reproductiva actualizada exitosamente', 'success')
        return redirect(url_for('historial_animal', animal_id=animal_id))
    
    return render_template('actualizar_reproductivo.html', animal=animal)

@app.route('/animal/<int:animal_id>/evento/registrar', methods=['GET', 'POST'])
@login_required
def registrar_evento(animal_id):
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    animal = Animal.query.get_or_404(animal_id)
    if animal.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('animales'))
    
    if request.method == 'POST':
        tipo_evento = request.form['tipo_evento']
        
        if tipo_evento == 'venta':
            animal.fecha_venta = datetime.strptime(request.form['fecha_venta'], '%Y-%m-%d').date()
            animal.comprador = request.form['comprador']
            animal.peso_venta = float(request.form['peso_venta'])
            animal.precio_venta = float(request.form['precio_venta'])
            animal.estado = 'vendido'
        elif tipo_evento == 'fallecimiento':
            animal.fecha_fallecimiento = datetime.strptime(request.form['fecha_fallecimiento'], '%Y-%m-%d').date()
            animal.causa_fallecimiento = request.form['causa_fallecimiento']
            animal.disposicion_final = request.form['disposicion_final']
            animal.estado = 'muerto'
        elif tipo_evento == 'cambio_estado':
            animal.estado = request.form['nuevo_estado']
        
        db.session.commit()
        flash('Evento registrado exitosamente', 'success')
        return redirect(url_for('historial_animal', animal_id=animal_id))
    
    return render_template('registrar_evento.html', animal=animal)

# Rutas para Eventos de Salud Integral
@app.route('/eventos_salud')
@login_required
def eventos_salud():
    """Vista principal de eventos de salud"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para ver eventos de salud')
        return redirect(url_for('fincas'))
    
    finca_id = session['finca_id']
    print(f"DEBUG: Finca ID desde sesión: {finca_id}")
    
    # Versión simplificada para debug
    try:
        # Contar todos los eventos sin filtros primero
        total_eventos_nuevos = db.session.query(EventoSalud).join(Animal).filter(
            Animal.finca_id == finca_id
        ).count()
        
        total_eventos_historial = db.session.query(HistorialSalud).join(Animal).filter(
            Animal.finca_id == finca_id
        ).count()
        
        print(f"DEBUG: Total eventos nuevos en finca {finca_id}: {total_eventos_nuevos}")
        print(f"DEBUG: Total eventos historial en finca {finca_id}: {total_eventos_historial}")
        
        # Si no hay eventos, mostrar mensaje específico
        if total_eventos_nuevos == 0 and total_eventos_historial == 0:
            print("DEBUG: No hay eventos de salud en esta finca")
            flash('No hay eventos de salud registrados en esta finca', 'info')
            return render_template('eventos_salud.html', 
                                eventos_salud=[],
                                total_eventos=0,
                                eventos_enfermedad=0,
                                eventos_partos=0,
                                eventos_vacunacion=0,
                                eventos_pendientes=0)
        
        # Obtener eventos (sin filtros por ahora)
        eventos_nuevos = db.session.query(EventoSalud, Animal).join(Animal).filter(
            Animal.finca_id == finca_id
        ).order_by(EventoSalud.fecha_evento.desc()).limit(10).all()
        
        eventos_historial = db.session.query(HistorialSalud, Animal).join(Animal).filter(
            Animal.finca_id == finca_id
        ).order_by(HistorialSalud.fecha_inicio.desc()).limit(10).all()
        
        print(f"DEBUG: Eventos nuevos obtenidos: {len(eventos_nuevos)}")
        print(f"DEBUG: Eventos historial obtenidos: {len(eventos_historial)}")
        
        # Combinar eventos
        eventos_salud = []
        
        for evento, animal in eventos_nuevos:
            print(f"DEBUG: Procesando evento nuevo - ID: {evento.id}, Tipo: {evento.tipo_evento}")
            eventos_salud.append({
                'tipo': 'nuevo',
                'evento': evento,
                'animal': animal,
                'fecha': evento.fecha_evento,
                'titulo': evento.titulo,
                'tipo_evento': evento.tipo_evento,
                'estado': evento.estado,
                'veterinario': evento.veterinario
            })
        
        for evento, animal in eventos_historial:
            print(f"DEBUG: Procesando evento historial - ID: {evento.id}, Tipo: {evento.tipo_evento}")
            eventos_salud.append({
                'tipo': 'historial',
                'evento': evento,
                'animal': animal,
                'fecha': evento.fecha_inicio,
                'titulo': evento.descripcion[:50] + '...' if len(evento.descripcion) > 50 else evento.descripcion,
                'tipo_evento': evento.tipo_evento,
                'estado': evento.estado or 'activo',
                'veterinario': evento.veterinario
            })
        
        print(f"DEBUG: Total eventos combinados: {len(eventos_salud)}")
        
        # Estadísticas
        total_eventos = len(eventos_salud)
        eventos_enfermedad = len([e for e in eventos_salud if e['tipo_evento'] == 'enfermedad'])
        eventos_partos = len([e for e in eventos_salud if e['tipo_evento'] == 'parto'])
        eventos_vacunacion = len([e for e in eventos_salud if 'vacun' in str(e['tipo_evento']).lower()])
        eventos_pendientes = len([e for e in eventos_salud if e['estado'] == 'pendiente'])
        
        print(f"DEBUG: Estadísticas - Total: {total_eventos}, Enfermedad: {eventos_enfermedad}, Partos: {eventos_partos}, Vacunación: {eventos_vacunacion}")
        
        return render_template('eventos_salud.html', 
                            eventos_salud=eventos_salud,
                            total_eventos=total_eventos,
                            eventos_enfermedad=eventos_enfermedad,
                            eventos_partos=eventos_partos,
                            eventos_vacunacion=eventos_vacunacion,
                            eventos_pendientes=eventos_pendientes)
    
    except Exception as e:
        print(f"ERROR en eventos_salud: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error al cargar eventos: {str(e)}', 'error')
        return render_template('eventos_salud.html', 
                            eventos_salud=[],
                            total_eventos=0,
                            eventos_enfermedad=0,
                            eventos_partos=0,
                            eventos_vacunacion=0,
                            eventos_pendientes=0)

@app.route('/eventos_salud/nuevo', methods=['GET', 'POST'])
@login_required
def eventos_salud_nuevo():
    """Crear un nuevo evento de salud"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    finca_id = session['finca_id']
    animales = Animal.query.filter_by(finca_id=finca_id).filter(Animal.estado.in_(['activo'])).all()
    veterinarios = Empleado.query.filter(Empleado.finca_id == finca_id, Empleado.cargo.like('%veterinario%')).all()
    
    if request.method == 'POST':
        try:
            evento_salud = EventoSalud(
                animal_id=request.form['animal_id'],
                tipo_evento=request.form['tipo_evento'],
                titulo=request.form['titulo'],
                descripcion=request.form['descripcion'],
                fecha_evento=datetime.strptime(request.form['fecha_evento'], '%Y-%m-%d').date(),
                hora_evento=datetime.strptime(request.form.get('hora_evento', '12:00'), '%H:%M').time(),
                estado=request.form.get('estado', 'pendiente'),
                diagnostico=request.form.get('diagnostico'),
                tratamiento=request.form.get('tratamiento'),
                medicamento=request.form.get('medicamento'),
                dosis=request.form.get('dosis'),
                via_administracion=request.form.get('via_administracion'),
                duracion_tratamiento=int(request.form['duracion_tratamiento']) if request.form.get('duracion_tratamiento') else None,
                proxima_dosis=datetime.strptime(request.form['proxima_dosis'], '%Y-%m-%d').date() if request.form.get('proxima_dosis') else None,
                tipo_parto=request.form.get('tipo_parto'),
                numero_crias=int(request.form['numero_crias']) if request.form.get('numero_crias') else None,
                crias_vivas=int(request.form['crias_vivas']) if request.form.get('crias_vivas') else None,
                crias_muertas=int(request.form['crias_muertas']) if request.form.get('crias_muertas') else None,
                peso_crias=float(request.form['peso_crias']) if request.form.get('peso_crias') else None,
                complicaciones=request.form.get('complicaciones'),
                tipo_vacuna=request.form.get('tipo_vacuna'),
                lote_vacuna=request.form.get('lote_vacuna'),
                fecha_proxima_dosis=datetime.strptime(request.form['fecha_proxima_dosis'], '%Y-%m-%d').date() if request.form.get('fecha_proxima_dosis') else None,
                veterinario=request.form.get('veterinario'),
                responsable=request.form.get('responsable'),
                resultado=request.form.get('resultado'),
                observaciones=request.form.get('observaciones'),
                fecha_recuperacion=datetime.strptime(request.form['fecha_recuperacion'], '%Y-%m-%d').date() if request.form.get('fecha_recuperacion') else None,
                usuario_registro=current_user.username if current_user.is_authenticated else 'sistema'
            )
            
            db.session.add(evento_salud)
            db.session.commit()
            flash('Evento de salud registrado exitosamente', 'success')
            return redirect(url_for('eventos_salud'))
            
        except Exception as e:
            flash(f'Error al registrar el evento: {str(e)}', 'danger')
            return redirect(url_for('eventos_salud_nuevo'))
    
    return render_template('nuevo_evento_salud.html', animales=animales, veterinarios=veterinarios)

@app.route('/eventos_salud/<int:evento_id>/editar', methods=['GET', 'POST'])
@login_required
def eventos_salud_editar(evento_id):
    """Editar un evento de salud existente"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    evento = EventoSalud.query.get_or_404(evento_id)
    
    # Verificar que el evento pertenezca a un animal de la finca actual
    if evento.animal.finca_id != session['finca_id']:
        flash('Acción no autorizada', 'danger')
        return redirect(url_for('eventos_salud'))
    
    finca_id = session['finca_id']
    animales = Animal.query.filter_by(finca_id=finca_id).filter(Animal.estado.in_(['activo'])).all()
    veterinarios = Empleado.query.filter(Empleado.finca_id == finca_id, Empleado.cargo.like('%veterinario%')).all()
    
    if request.method == 'POST':
        try:
            evento.tipo_evento = request.form['tipo_evento']
            evento.titulo = request.form['titulo']
            evento.descripcion = request.form['descripcion']
            evento.fecha_evento = datetime.strptime(request.form['fecha_evento'], '%Y-%m-%d').date()
            evento.hora_evento = datetime.strptime(request.form.get('hora_evento', '12:00'), '%H:%M').time()
            evento.estado = request.form.get('estado', 'pendiente')
            evento.diagnostico = request.form.get('diagnostico')
            evento.tratamiento = request.form.get('tratamiento')
            evento.medicamento = request.form.get('medicamento')
            evento.dosis = request.form.get('dosis')
            evento.via_administracion = request.form.get('via_administracion')
            evento.duracion_tratamiento = int(request.form['duracion_tratamiento']) if request.form.get('duracion_tratamiento') else None
            evento.proxima_dosis = datetime.strptime(request.form['proxima_dosis'], '%Y-%m-%d').date() if request.form.get('proxima_dosis') else None
            evento.tipo_parto = request.form.get('tipo_parto')
            evento.numero_crias = int(request.form['numero_crias']) if request.form.get('numero_crias') else None
            evento.crias_vivas = int(request.form['crias_vivas']) if request.form.get('crias_vivas') else None
            evento.crias_muertas = int(request.form['crias_muertas']) if request.form.get('crias_muertas') else None
            evento.peso_crias = float(request.form['peso_crias']) if request.form.get('peso_crias') else None
            evento.complicaciones = request.form.get('complicaciones')
            evento.tipo_vacuna = request.form.get('tipo_vacuna')
            evento.lote_vacuna = request.form.get('lote_vacuna')
            evento.fecha_proxima_dosis = datetime.strptime(request.form['fecha_proxima_dosis'], '%Y-%m-%d').date() if request.form.get('fecha_proxima_dosis') else None
            evento.veterinario = request.form.get('veterinario')
            evento.responsable = request.form.get('responsable')
            evento.resultado = request.form.get('resultado')
            evento.observaciones = request.form.get('observaciones')
            evento.fecha_recuperacion = datetime.strptime(request.form['fecha_recuperacion'], '%Y-%m-%d').date() if request.form.get('fecha_recuperacion') else None
            
            db.session.commit()
            flash('Evento de salud actualizado exitosamente', 'success')
            return redirect(url_for('eventos_salud'))
            
        except Exception as e:
            flash(f'Error al actualizar el evento: {str(e)}', 'danger')
            return redirect(url_for('eventos_salud_editar', evento_id=evento_id))
    
    return render_template('editar_evento_salud.html', evento=evento, animales=animales, veterinarios=veterinarios)

@app.route('/eventos_salud/<int:evento_id>/imagenes')
@login_required
def eventos_salud_imagenes(evento_id):
    """Vista para gestionar imágenes de un evento de salud"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    evento = EventoSalud.query.get_or_404(evento_id)
    
    # Verificar que el evento pertenezca a un animal de la finca actual
    if evento.animal.finca_id != session['finca_id']:
        flash('Acción no autorizada', 'danger')
        return redirect(url_for('eventos_salud'))
    
    imagenes = ImagenEventoSalud.query.filter_by(evento_salud_id=evento_id).order_by(ImagenEventoSalud.fecha_subida.desc()).all()
    
    return render_template('imagenes_evento_salud.html', evento=evento, imagenes=imagenes)

@app.route('/eventos_salud/<int:evento_id>/imagenes/subir', methods=['POST'])
@login_required
def subir_imagen_evento_salud(evento_id):
    """Subir una imagen para un evento de salud"""
    try:
        if 'finca_id' not in session:
            return jsonify({'error': 'No autorizado'}), 403
        
        evento = EventoSalud.query.get_or_404(evento_id)
        
        if evento.animal.finca_id != session['finca_id']:
            return jsonify({'error': 'No autorizado'}), 403
        
        if 'imagen' not in request.files:
            return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        
        file = request.files['imagen']
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        
        print(f"Archivo recibido: {file.filename}")
        print(f"Tipo de archivo: {file.content_type}")
        
        if file and allowed_file(file.filename):
            # Crear directorio si no existe
            upload_dir = os.path.join('static', 'imagenes_eventos_salud', str(evento_id))
            print(f"Directorio de subida: {upload_dir}")
            
            try:
                os.makedirs(upload_dir, exist_ok=True)
                print("Directorio creado exitosamente")
            except Exception as e:
                print(f"Error al crear directorio: {e}")
                return jsonify({'error': f'Error al crear directorio: {str(e)}'}), 500
            
            # Generar nombre único
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            
            file_path = os.path.join(upload_dir, unique_filename)
            print(f"Ruta del archivo: {file_path}")
            
            try:
                # Guardar archivo
                file.save(file_path)
                print("Archivo guardado exitosamente")
                
                # Verificar que el archivo se guardó
                if not os.path.exists(file_path):
                    return jsonify({'error': 'El archivo no se pudo guardar'}), 500
                    
                file_size = os.path.getsize(file_path)
                print(f"Tamaño del archivo guardado: {file_size} bytes")
                
            except Exception as e:
                print(f"Error al guardar archivo: {e}")
                return jsonify({'error': f'Error al guardar archivo: {str(e)}'}), 500
            
            try:
                # Guardar en base de datos con ruta relativa y forward slashes
                ruta_relativa = os.path.join('imagenes_eventos_salud', str(evento_id), unique_filename).replace('\\', '/')
                nueva_imagen = ImagenEventoSalud(
                    evento_salud_id=evento_id,
                    nombre_archivo=filename,
                    ruta_archivo=ruta_relativa,
                    descripcion=request.form.get('descripcion', ''),
                    usuario_registro=current_user.username if current_user.is_authenticated else 'sistema'
                )
                
                db.session.add(nueva_imagen)
                db.session.commit()
                print("Registro guardado en base de datos")
                
            except Exception as e:
                print(f"Error en base de datos: {e}")
                # Eliminar archivo si falla la base de datos
                if os.path.exists(file_path):
                    os.remove(file_path)
                return jsonify({'error': f'Error en base de datos: {str(e)}'}), 500
            
            return jsonify({
                'success': True,
                'message': 'Imagen subida exitosamente',
                'imagen': {
                    'id': nueva_imagen.id,
                    'nombre': nueva_imagen.nombre_archivo,
                    'descripcion': nueva_imagen.descripcion,
                    'fecha': nueva_imagen.fecha_subida.strftime('%d/%m/%Y %H:%M'),
                    'ruta': '/static/' + nueva_imagen.ruta_archivo
                }
            })
        
        return jsonify({'error': 'Tipo de archivo no permitido'}), 400
    
    except Exception as e:
        print(f"Error general en subir_imagen_evento_salud: {e}")
        return jsonify({'error': f'Error general: {str(e)}'}), 500

@app.route('/eventos_salud/imagenes/<int:imagen_id>/eliminar', methods=['POST'])
@login_required
def eliminar_imagen_evento_salud(imagen_id):
    """Eliminar una imagen de evento de salud"""
    imagen = ImagenEventoSalud.query.get_or_404(imagen_id)
    
    # Verificar permisos
    if imagen.evento.animal.finca_id != session['finca_id']:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        # Construir la ruta completa del archivo
        file_path = os.path.join('static', imagen.ruta_archivo)
        
        # Eliminar archivo del sistema
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Eliminar registro de la base de datos
        db.session.delete(imagen)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Imagen eliminada exitosamente'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al eliminar la imagen: {str(e)}'}), 500

@app.route('/eventos_salud/imagenes/<int:imagen_id>/descargar')
@login_required
def descargar_imagen_evento_salud(imagen_id):
    """Descargar una imagen de evento de salud"""
    imagen = ImagenEventoSalud.query.get_or_404(imagen_id)
    
    # Verificar permisos
    if imagen.evento.animal.finca_id != session['finca_id']:
        flash('Acción no autorizada', 'danger')
        return redirect(url_for('eventos_salud'))
    
    # Construir la ruta completa del archivo
    file_path = os.path.join('static', imagen.ruta_archivo)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=imagen.nombre_archivo)
    else:
        flash('La imagen no existe', 'danger')
        return redirect(url_for('eventos_salud_imagenes', evento_id=imagen.evento_salud_id))

def allowed_file(filename):
    """Verificar si el archivo es una imagen permitida"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/eventos_salud/<int:evento_id>/eliminar', methods=['POST'])
@login_required
def eventos_salud_eliminar(evento_id):
    """Eliminar un evento de salud"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    evento = EventoSalud.query.get_or_404(evento_id)
    
    # Verificar que el evento pertenezca a un animal de la finca actual
    if evento.animal.finca_id != session['finca_id']:
        flash('Acción no autorizada', 'danger')
        return redirect(url_for('eventos_salud'))
    
    try:
        # First, delete all associated images manually
        imagenes = ImagenEventoSalud.query.filter_by(evento_salud_id=evento_id).all()
        
        for imagen in imagenes:
            # Delete image file from filesystem
            file_path = os.path.join('static', imagen.ruta_archivo)
            if os.path.exists(file_path):
                os.remove(file_path)
            # Delete image record from database
            db.session.delete(imagen)
        
        # Now delete the event
        db.session.delete(evento)
        db.session.commit()
        flash('Evento de salud eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el evento: {str(e)}', 'danger')
    
    return redirect(url_for('eventos_salud'))

@app.route('/eventos_salud/<int:evento_id>/ver')
@login_required
def eventos_salud_ver(evento_id):
    """Ver detalles de un evento de salud"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    evento = EventoSalud.query.get_or_404(evento_id)
    
    # Verificar que el evento pertenezca a un animal de la finca actual
    if evento.animal.finca_id != session['finca_id']:
        flash('Acción no autorizada', 'danger')
        return redirect(url_for('eventos_salud'))
    
    return render_template('ver_evento_salud.html', evento=evento, dt=datetime)

@app.route('/reporte/eventos_salud/pdf')
@login_required
def reporte_eventos_salud_pdf():
    """Genera un reporte PDF de eventos de salud"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib import colors
        from io import BytesIO
        
        finca_id = session['finca_id']
        finca = Finca.query.get(finca_id)
        
        # Obtener todos los eventos de salud de la finca
        eventos_salud = db.session.query(EventoSalud, Animal).join(Animal).filter(
            Animal.finca_id == finca_id
        ).order_by(EventoSalud.fecha_evento.desc()).all()
        
        # Crear el documento PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Contenido del PDF
        story = []
        
        # Título
        story.append(Paragraph(f"Reporte de Eventos de Salud<br/>{finca.nombre}", title_style))
        story.append(Spacer(1, 20))
        
        # Fecha del reporte
        story.append(Paragraph(f"<b>Fecha del reporte:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Estadísticas
        total_eventos = len(eventos_salud)
        eventos_enfermedad = len([e for e, a in eventos_salud if e.tipo_evento == 'enfermedad'])
        eventos_partos = len([e for e, a in eventos_salud if e.tipo_evento == 'parto'])
        eventos_vacunacion = len([e for e, a in eventos_salud if e.tipo_evento == 'vacunacion'])
        
        stats_data = [
            ['Estadística', 'Cantidad'],
            ['Total de Eventos', str(total_eventos)],
            ['Eventos de Enfermedad', str(eventos_enfermedad)],
            ['Eventos de Parto', str(eventos_partos)],
            ['Eventos de Vacunación', str(eventos_vacunacion)]
        ]
        
        stats_table = Table(stats_data, colWidths=[8*cm, 3*cm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Tabla de eventos
        if eventos_salud:
            story.append(Paragraph("<b>Detalle de Eventos de Salud</b>", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            eventos_data = [['Fecha', 'Animal', 'Tipo', 'Título', 'Estado', 'Veterinario']]
            
            for evento, animal in eventos_salud:
                eventos_data.append([
                    evento.fecha_evento.strftime('%d/%m/%Y'),
                    animal.identificacion,
                    evento.tipo_evento.title(),
                    evento.titulo[:30] + '...' if len(evento.titulo) > 30 else evento.titulo,
                    evento.estado.title(),
                    evento.veterinario or 'N/A'
                ])
            
            eventos_table = Table(eventos_data, colWidths=[2.5*cm, 2*cm, 2.5*cm, 4*cm, 2*cm, 2.5*cm])
            eventos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8)
            ]))
            
            story.append(eventos_table)
        else:
            story.append(Paragraph("No se encontraron eventos de salud registrados.", styles['Normal']))
        
        # Generar PDF
        doc.build(story)
        
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'reporte_eventos_salud_{finca.nombre}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Error al generar el reporte: {str(e)}', 'danger')
        return redirect(url_for('eventos_salud'))

@app.route('/exportar/animales')
@login_required
def exportar_animales():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    animales = Animal.query.filter_by(finca_id=session['finca_id']).filter(Animal.estado.in_(['activo'])).all()
    df = pd.DataFrame([{k: getattr(a, k) for k in ['id','identificacion','tipo','raza','fecha_nacimiento','peso','estado','potrero_id','fecha_ingreso','imagen']} for a in animales])
    return df.to_excel('animales.xlsx', index=False), 200, {'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Content-Disposition': 'attachment; filename=animales.xlsx'}

def generate_vaccination_report(finca_id):
    """Genera los datos para el reporte de vacunación"""
    # Obtener datos de la base de datos
    finca = Finca.query.get(finca_id)
    
    # Obtener todas las vacunas ordenadas por fecha de próxima dosis
    vacunas = Vacuna.query.filter_by(finca_id=finca_id)\
                         .order_by(Vacuna.fecha_proxima.asc())\
                         .all()
    
    # Animales sin vacunar (que no tienen vacunas registradas)
    animales_sin_vacunar = Animal.query.filter(
        Animal.finca_id == finca_id,
        ~Animal.id.in_(db.session.query(Vacuna.animal_id).filter(Vacuna.finca_id == finca_id))
    ).order_by(Animal.identificacion).all()
    
    # Obtener todos los animales para verificar vacunación
    todos_animales = Animal.query.filter_by(finca_id=finca_id).filter(Animal.estado.in_(['activo'])).all()
    
    # Agrupar vacunas por tipo para el reporte
    vacunas_por_tipo = {}
    for vacuna in vacunas:
        if vacuna.tipo_vacuna not in vacunas_por_tipo:
            vacunas_por_tipo[vacuna.tipo_vacuna] = []
        vacunas_por_tipo[vacuna.tipo_vacuna].append(vacuna)
    
    # Obtener vacunas agrupadas por animal con detalles del aplicador
    vacunas_por_animal = {}
    for animal in todos_animales:
        vacunas_animal = Vacuna.query.filter_by(animal_id=animal.id)\
                                   .join(Empleado, Vacuna.empleado_id == Empleado.id, isouter=True)\
                                   .all()
        if vacunas_animal:
            vacunas_por_animal[animal.id] = {
                'animal': animal,
                'vacunas': sorted(vacunas_animal, key=lambda x: x.fecha_proxima, reverse=True)
            }
    
    # Obtener empleados que han aplicado vacunas
    empleados_vacunadores = {}
    for vacuna in vacunas:
        if vacuna.empleado_id and vacuna.empleado_id not in empleados_vacunadores:
            empleado = Empleado.query.get(vacuna.empleado_id)
            if empleado:
                empleados_vacunadores[vacuna.empleado_id] = {
                    'nombre': f"{empleado.nombre} {empleado.apellido}",
                    'cargo': empleado.cargo,
                    'vacunas_aplicadas': Vacuna.query.filter_by(empleado_id=vacuna.empleado_id).count()
                }
    
    # Obtener próximas vacunas a aplicar (próximos 30 días)
    from datetime import timedelta
    fecha_limite = date.today() + timedelta(days=30)
    proximas_vacunas = Vacuna.query.filter(
        Vacuna.finca_id == finca_id,
        Vacuna.fecha_proxima <= fecha_limite,
        Vacuna.fecha_proxima >= date.today()
    ).order_by(Vacuna.fecha_proxima.asc()).all()
    
    # Obtener registro detallado de vacunas aplicadas con información completa
    registro_vacunas_aplicadas = []
    for vacuna in vacunas:
        aplicador_info = "No especificado"
        if vacuna.empleado_id:
            empleado = Empleado.query.get(vacuna.empleado_id)
            if empleado:
                aplicador_info = f"{empleado.nombre} {empleado.apellido} ({empleado.cargo or 'Empleado'})"
        
        registro_vacunas_aplicadas.append({
            'animal_id': vacuna.animal.id,
            'animal_identificacion': vacuna.animal.identificacion,
            'animal_nombre': vacuna.animal.nombre or 'Sin nombre',
            'animal_tipo': vacuna.animal.tipo,
            'tipo_vacuna': vacuna.tipo_vacuna,
            'fecha_aplicacion': vacuna.fecha_aplicacion,
            'fecha_proxima': vacuna.fecha_proxima,
            'aplicada_por': vacuna.aplicada_por,
            'aplicador_info': aplicador_info,
            'numero_lote': vacuna.numero_lote,
            'fecha_vencimiento': vacuna.fecha_vencimiento,
            'observaciones': vacuna.observaciones
        })
    
    # Obtener registro de vacunas por aplicar (animales que necesitan vacunas)
    vacunas_por_aplicar = []
    for animal in animales_sin_vacunar:
        # Calcular edad para determinar si necesita vacunas básicas
        if animal.fecha_nacimiento:
            edad_meses = (date.today() - animal.fecha_nacimiento).days // 30
            if edad_meses < 6:
                vacunas_recomendadas = "Vacunas básicas para crías (Triple, Bovilis, etc.)"
            elif edad_meses < 12:
                vacunas_recomendadas = "Refuerzo de vacunas básicas"
            else:
                vacunas_recomendadas = "Mantenimiento anual (Triple, Rabia, etc.)"
        else:
            vacunas_recomendadas = "Consultar historial de vacunación"
        
        vacunas_por_aplicar.append({
            'animal_id': animal.id,
            'animal_identificacion': animal.identificacion,
            'animal_nombre': animal.nombre or 'Sin nombre',
            'animal_tipo': animal.tipo,
            'animal_sexo': animal.sexo or 'N/A',
            'animal_edad': f"{edad_meses} meses" if animal.fecha_nacimiento else 'N/A',
            'ubicacion': animal.ubicacion_asignada.nombre if animal.ubicacion_asignada else 'Sin ubicación',
            'vacunas_recomendadas': vacunas_recomendadas,
            'prioridad': 'Alta' if edad_meses < 6 else 'Media'
        })
    
    return {
        'finca': finca,
        'vacunas': vacunas,
        'animales_sin_vacunar': animales_sin_vacunar,
        'vacunas_por_tipo': vacunas_por_tipo,
        'vacunas_por_animal': vacunas_por_animal,
        'empleados_vacunadores': empleados_vacunadores,
        'total_animales': len(todos_animales),
        'fecha_reporte': date.today(),
        'proximas_vacunas': proximas_vacunas,
        'registro_vacunas_aplicadas': registro_vacunas_aplicadas,
        'vacunas_por_aplicar': vacunas_por_aplicar
    }

@app.route('/reporte/vacunas/pdf')
@login_required
def reporte_vacunas_pdf():
    """Genera un reporte PDF de vacunación con animales vacunados y pendientes"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib import colors
        from io import BytesIO
        
        # Obtener datos para el reporte
        report_data = generate_vaccination_report(session['finca_id'])
        finca = report_data['finca']
        vacunas = report_data['vacunas']
        animales_sin_vacunar = report_data['animales_sin_vacunar']
        vacunas_por_tipo = report_data['vacunas_por_tipo']
        registro_vacunas_aplicadas = report_data['registro_vacunas_aplicadas']
        vacunas_por_aplicar = report_data['vacunas_por_aplicar']
        proximas_vacunas = report_data['proximas_vacunas']
        
        # Crear el documento PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title=f'Reporte de Vacunación - {finca.nombre}'
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilo para el título
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Estilo para subtítulos
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Contenido del PDF
        elements = []
        
        # Título principal
        elements.append(Paragraph(f'Reporte de Vacunación - {finca.nombre}', title_style))
        elements.append(Paragraph(f'Generado el: {date.today().strftime("%d/%m/%Y")}', styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Resumen
        elements.append(Paragraph('Resumen de Vacunación', subtitle_style))
        
        # Datos del resumen
        resumen_data = [
            ['Total de vacunas aplicadas:', str(len(vacunas))],
            ['Animales pendientes de vacunación:', ''],
            ['Tipos de vacunas aplicadas:', str(len(vacunas_por_tipo))]
        ]
        
        # Tabla de resumen
        resumen_table = Table(resumen_data, colWidths=[doc.width/2.0]*2)
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.HexColor('#6c757d')),
        ]))
        
        elements.append(resumen_table)
        elements.append(Spacer(1, 20))
        
        # Sección 1: Registro Detallado de Vacunas Aplicadas
        if registro_vacunas_aplicadas:
            elements.append(Paragraph('Registro Detallado de Vacunas Aplicadas', subtitle_style))
            
            # Datos de la tabla de vacunas aplicadas
            data_aplicadas = [
                ['ID Animal', 'Identificación', 'Nombre', 'Tipo', 'Vacuna', 'Fecha Aplicación', 'Próxima Dosis', 'Aplicado Por']
            ]
            
            for registro in registro_vacunas_aplicadas:
                data_aplicadas.append([
                    str(registro['animal_id']),
                    registro['animal_identificacion'],
                    registro['animal_nombre'],
                    registro['animal_tipo'],
                    registro['tipo_vacuna'],
                    registro['fecha_aplicacion'].strftime('%d/%m/%Y'),
                    registro['fecha_proxima'].strftime('%d/%m/%Y'),
                    registro['aplicador_info']
                ])
            
            # Ajustar anchos de columna para mejor visualización
            col_widths_aplicadas = [
                doc.width * 0.08,  # ID Animal
                doc.width * 0.12,  # Identificación
                doc.width * 0.12,  # Nombre
                doc.width * 0.08,  # Tipo
                doc.width * 0.15,  # Vacuna
                doc.width * 0.12,  # Fecha Aplicación
                doc.width * 0.12,  # Próxima Dosis
                doc.width * 0.21   # Aplicado Por
            ]
            
            tabla_aplicadas = Table(data_aplicadas, colWidths=col_widths_aplicadas)
            tabla_aplicadas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f9ff')),
                ('FONTSIZE', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(tabla_aplicadas)
            elements.append(Spacer(1, 15))
        
        # Sección 2: Vacunas por Aplicar
        if vacunas_por_aplicar:
            elements.append(Paragraph('Vacunas por Aplicar', subtitle_style))
            
            # Resumen de vacunas por aplicar
            resumen_por_aplicar = [
                ['Total de animales sin vacunar:', str(len(vacunas_por_aplicar))],
                ['Prioridad alta (crías < 6 meses):', str(len([v for v in vacunas_por_aplicar if v['prioridad'] == 'Alta']))],
                ['Prioridad media:', str(len([v for v in vacunas_por_aplicar if v['prioridad'] == 'Media']))]
            ]
            
            resumen_table = Table(resumen_por_aplicar, colWidths=[doc.width/2.0]*2)
            resumen_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fef3c7')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#fbbf24')),
            ]))
            
            elements.append(resumen_table)
            elements.append(Spacer(1, 10))
            
            # Datos de la tabla de vacunas por aplicar
            data_por_aplicar = [
                ['ID', 'Identificación', 'Nombre', 'Tipo', 'Sexo', 'Edad', 'Ubicación', 'Vacunas Recomendadas', 'Prioridad']
            ]
            
            for registro in vacunas_por_aplicar:
                data_por_aplicar.append([
                    str(registro['animal_id']),
                    registro['animal_identificacion'],
                    registro['animal_nombre'],
                    registro['animal_tipo'],
                    registro['animal_sexo'],
                    registro['animal_edad'],
                    registro['ubicacion'],
                    registro['vacunas_recomendadas'],
                    registro['prioridad']
                ])
            
            # Ajustar anchos de columna
            col_widths_por_aplicar = [
                doc.width * 0.05,  # ID
                doc.width * 0.12,  # Identificación
                doc.width * 0.10,  # Nombre
                doc.width * 0.08,  # Tipo
                doc.width * 0.06,  # Sexo
                doc.width * 0.08,  # Edad
                doc.width * 0.12,  # Ubicación
                doc.width * 0.24,  # Vacunas Recomendadas
                doc.width * 0.15   # Prioridad
            ]
            
            tabla_por_aplicar = Table(data_por_aplicar, colWidths=col_widths_por_aplicar)
            tabla_por_aplicar.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 6),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fef2f2')),
                ('FONTSIZE', (0, 1), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fecaca')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(tabla_por_aplicar)
            elements.append(Spacer(1, 15))
        
        # Sección 3: Próximas Vacunas (Próximos 30 días)
        if proximas_vacunas:
            elements.append(Paragraph('Próximas Vacunas (Próximos 30 días)', subtitle_style))
            
            # Datos de la tabla de próximas vacunas
            data_proximas = [
                ['ID Animal', 'Identificación', 'Nombre', 'Tipo Vacuna', 'Fecha Próxima Dosis', 'Días Restantes', 'Aplicado Por']
            ]
            
            for vacuna in proximas_vacunas:
                dias_restantes = (vacuna.fecha_proxima - date.today()).days
                aplicador_info = "No especificado"
                if vacuna.empleado_id:
                    empleado = Empleado.query.get(vacuna.empleado_id)
                    if empleado:
                        aplicador_info = f"{empleado.nombre} {empleado.apellido}"
                
                data_proximas.append([
                    str(vacuna.animal.id),
                    vacuna.animal.identificacion,
                    vacuna.animal.nombre or 'Sin nombre',
                    vacuna.tipo_vacuna,
                    vacuna.fecha_proxima.strftime('%d/%m/%Y'),
                    f"{dias_restantes} días",
                    aplicador_info
                ])
            
            # Ajustar anchos de columna
            col_widths_proximas = [
                doc.width * 0.08,  # ID Animal
                doc.width * 0.15,  # Identificación
                doc.width * 0.15,  # Nombre
                doc.width * 0.20,  # Tipo Vacuna
                doc.width * 0.15,  # Fecha Próxima Dosis
                doc.width * 0.12,  # Días Restantes
                doc.width * 0.15   # Aplicado Por
            ]
            
            tabla_proximas = Table(data_proximas, colWidths=col_widths_proximas)
            tabla_proximas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3e8ff')),
                ('FONTSIZE', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d8b4fe')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(tabla_proximas)
            elements.append(Spacer(1, 15))
        
        # Sección de vacunas por tipo
        for tipo_vacuna, vacunas_tipo in vacunas_por_tipo.items():
            elements.append(PageBreak())
            elements.append(Paragraph(f'Vacuna: {tipo_vacuna}', subtitle_style))
            
            # Datos de la tabla
            data = [
                ['ID Animal', 'Identificación', 'Nombre', 'Fecha Aplicación', 'Próxima Dosis', 'Aplicada Por', 'Lote', 'Vencimiento']
            ]
            
            for vacuna in vacunas_tipo:
                aplicador_info = "No especificado"
                if vacuna.empleado_id:
                    empleado = Empleado.query.get(vacuna.empleado_id)
                    if empleado:
                        aplicador_info = f"{empleado.nombre} {empleado.apellido}"
                
                data.append([
                    str(vacuna.animal.id),
                    vacuna.animal.identificacion,
                    vacuna.animal.nombre or 'Sin nombre',
                    vacuna.fecha_aplicacion.strftime('%d/%m/%Y'),
                    vacuna.fecha_proxima.strftime('%d/%m/%Y'),
                    aplicador_info,
                    vacuna.numero_lote or 'N/A',
                    vacuna.fecha_vencimiento.strftime('%d/%m/%Y') if vacuna.fecha_vencimiento else 'N/A'
                ])
            
            # Crear tabla
            table = Table(data, colWidths=[doc.width/8.0]*8)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.HexColor('#6c757d')),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 10))
            
            # Estadísticas de la vacuna
            stats = [
                ['Total de dosis aplicadas:', str(len(vacunas_tipo))],
                ['Próxima dosis más cercana:', min([v.fecha_proxima for v in vacunas_tipo]).strftime('%d/%m/%Y') if vacunas_tipo else 'N/A']
            ]
            
            stats_table = Table(stats, colWidths=[doc.width/2.0]*2)
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ]))
            
            elements.append(stats_table)
        
        # Sección de resumen de vacunación
        elements.append(PageBreak())
        elements.append(Paragraph('Resumen General de Vacunación', subtitle_style))
        
        # Obtener todos los animales para el cálculo de porcentajes
        total_animales = report_data['total_animales']  # Usar el total real de animales
        animales_vacunados_unicos = len(set(v.animal_id for v in vacunas))  # Animales únicos vacunados
        porcentaje_vacunados = (animales_vacunados_unicos / total_animales * 100) if total_animales > 0 else 0
        
        # Datos del resumen general
        resumen_general = [
            ['Total de animales en la finca:', str(total_animales)],
            ['Total de vacunas aplicadas:', str(len(vacunas))],
            ['Animales vacunados (únicos):', f"({porcentaje_vacunados:.1f}%)"],
            ['Animales pendientes de vacunación:', f"({(100 - porcentaje_vacunados):.1f}%)"],
            ['Tipos de vacunas aplicadas:', str(len(vacunas_por_tipo))]
        ]
        
        resumen_table = Table(resumen_general, colWidths=[doc.width/2.0]*2)
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.HexColor('#6c757d')),
        ]))
        elements.append(resumen_table)
        elements.append(Spacer(1, 20))
        
        # Sección de personal de vacunación
        if report_data['empleados_vacunadores']:
            elements.append(Paragraph('Personal de Vacunación', subtitle_style))
            
            empleados_data = [
                ['Nombre', 'Cargo', 'Vacunas Aplicadas']
            ]
            
            for empleado in report_data['empleados_vacunadores'].values():
                empleados_data.append([
                    empleado['nombre'],
                    empleado['cargo'],
                    str(empleado['vacunas_aplicadas'])
                ])
            
            empleados_table = Table(empleados_data, colWidths=[doc.width/3.0]*3)
            empleados_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ebf5fb')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d6eaf8')),
            ]))
            elements.append(empleados_table)
            elements.append(Spacer(1, 20))
        
        # Sección de animales sin vacunar
        if animales_sin_vacunar:
            elements.append(PageBreak())
            elements.append(Paragraph('Animales Pendientes de Vacunación', subtitle_style))
            
            # Resumen de animales sin vacunar
            resumen_sin_vacunar = [
                ['Total de animales sin vacunar:', str(len(animales_sin_vacunar))],
                ['Porcentaje del total:', f"{(len(animales_sin_vacunar)/total_animales*100):.1f}%" if total_animales > 0 else '0%']
            ]
            
            resumen_table = Table(resumen_sin_vacunar, colWidths=[doc.width/2.0]*2)
            resumen_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#fecaca')),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.HexColor('#dc2626')),
            ]))
            elements.append(resumen_table)
            elements.append(Spacer(1, 15))
            
            # Tabla de animales sin vacunar
            data = [
                ['ID', 'Identificación', 'Tipo', 'Sexo', 'Edad', 'Ubicación', 'Estado']
            ]
            
            for animal in sorted(animales_sin_vacunar, key=lambda x: x.identificacion):
                # Calcular edad en meses
                if animal.fecha_nacimiento:
                    meses = (date.today() - animal.fecha_nacimiento).days // 30
                    if meses < 12:
                        edad = f"{meses} meses"
                    else:
                        años = meses // 12
                        meses_resto = meses % 12
                        edad = f"{años} año{'s' if años > 1 else ''}"
                        if meses_resto > 0:
                            edad += f" {meses_resto} mes{'es' if meses_resto > 1 else ''}"
                else:
                    edad = 'N/A'
                
                data.append([
                    str(animal.id),
                    animal.identificacion,
                    animal.tipo or 'No especificado',
                    animal.sexo or 'N/A',
                    edad,
                    animal.ubicacion_asignada.nombre if animal.ubicacion_asignada else 'Sin ubicación',
                    animal.estado or 'Activo'
                ])
            
            # Ajustar ancho de columnas
            col_widths = [
                doc.width * 0.05,  # ID
                doc.width * 0.15,  # Identificación
                doc.width * 0.15,  # Tipo
                doc.width * 0.1,   # Sexo
                doc.width * 0.15,  # Edad
                doc.width * 0.2,   # Ubicación
                doc.width * 0.2    # Estado
            ]
            
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),  # Rojo para indicar pendientes
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fef2f2')),  # Fondo rojo claro
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fecaca')),  # Borde rojo claro
                ('BOX', (0, 0), (-1, -1), 0.25, colors.HexColor('#dc2626')),  # Borde rojo
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            # Ajustar el estilo para que el texto largo se ajuste
            for i in range(1, len(data)):
                table.setStyle(TableStyle([
                    ('FONTSIZE', (0, i), (-1, i), 6),
                    ('LEFTPADDING', (0, i), (-1, i), 2),
                    ('RIGHTPADDING', (0, i), (-1, i), 2),
                ]))
            
            elements.append(table)
        
        # Pie de página con información de la finca
        elements.append(Spacer(1, 20))
        from reportlab.platypus.flowables import HRFlowable
        elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.HexColor('#6c757d')))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"{finca.nombre} - {finca.direccion or ''}", styles['Italic']))
        elements.append(Paragraph(f"Teléfono: {finca.telefono or 'No especificado'} | Email: {finca.email or 'No especificado'}", styles['Italic']))
        elements.append(Paragraph(f"Reporte generado el {date.today().strftime('%d/%m/%Y')} a las {datetime.now().strftime('%H:%M')}", styles['Italic']))
        
        # Generar el PDF
        def add_page_number(canvas, doc):
            page_num = canvas.getPageNumber()
            text = f"Página {page_num}"
            canvas.saveState()
            canvas.setFont('Helvetica', 9)
            canvas.drawRightString(19.5*cm, 1*cm, text)
            canvas.restoreState()
        
        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        
        # Preparar la respuesta
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'reporte_vacunacion_{finca.nombre.lower().replace(" ", "_")}_{date.today().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error al generar el reporte de vacunación: {str(e)}")
        flash(f'Error al generar el reporte: {str(e)}', 'danger')
        return redirect(url_for('vacunas'))

@app.route('/reporte/animales/pdf')
@login_required
def reporte_animales_pdf():
    """Genera un reporte PDF de todos los animales de la finca"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.lib import colors
        from io import BytesIO
        from datetime import datetime
        
        finca_id = session['finca_id']
        finca = Finca.query.get(finca_id)
        finca_nombre = finca.nombre if finca else 'Sin nombre'
        
        # Obtener animales con información detallada
        animales = db.session.query(
            Animal.id,
            Animal.identificacion,
            Animal.nombre,
            Animal.tipo,
            Animal.raza,
            Animal.sexo,
            Animal.fecha_nacimiento,
            Animal.estado,
            Animal.peso,
            Animal.fecha_ingreso,
            Animal.fecha_venta,
            Animal.comprador
        ).filter(Animal.finca_id == finca_id).all()
        
        # Crear el documento PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title=f'Reporte de Animales - {finca_nombre}'
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilo para el título
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Estilo para subtítulos
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Contenido del PDF
        elements = []
        
        # Título principal
        elements.append(Paragraph(f'Reporte de Animales - {finca_nombre}', title_style))
        elements.append(Paragraph(f'Generado el: {datetime.now().strftime("%d/%m/%Y %H:%M")}', styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Resumen general
        elements.append(Paragraph('Resumen General', subtitle_style))
        
        total_animales = len(animales)
        animales_activos = len([a for a in animales if a.estado and a.estado.lower() == 'activo'])
        animales_vendidos = len([a for a in animales if a.estado and a.estado.lower() == 'vendido'])
        animales_fallecidos = len([a for a in animales if a.estado and (a.estado.lower() in ['muerto', 'fallecido'])])
        
        resumen_data = [
            ['Total de animales:', str(total_animales)],
            ['Animales activos:', str(animales_activos)],
            ['Animales vendidos:', str(animales_vendidos)],
            ['Animales fallecidos:', str(animales_fallecidos)]
        ]
        
        resumen_table = Table(resumen_data, colWidths=[doc.width/2.0]*2)
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.HexColor('#6c757d')),
        ]))
        
        elements.append(resumen_table)
        elements.append(Spacer(1, 20))
        
        # Tabla de animales
        elements.append(Paragraph('Detalle de Animales', subtitle_style))
        
        # Encabezados de la tabla
        headers = [
            'ID', 'Nombre', 'Tipo', 'Raza', 'Sexo', 
            'Fecha Nac.', 'Edad', 'Peso (kg)', 'Estado', 'Ingreso'
        ]
        
        # Función para calcular la edad
        def calcular_edad(fecha_nacimiento):
            if not fecha_nacimiento:
                return 'N/A'
            hoy = datetime.now().date()
            edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            return f"{edad} años"
        
        # Datos de la tabla
        data = [headers]
        for animal in animales:
            data.append([
                animal.identificacion or 'N/A',
                animal.nombre or 'Sin nombre',
                animal.tipo or 'N/A',
                animal.raza or 'N/A',
                animal.sexo or 'N/A',
                animal.fecha_nacimiento.strftime('%d/%m/%Y') if animal.fecha_nacimiento else 'N/A',
                calcular_edad(animal.fecha_nacimiento) if animal.fecha_nacimiento else 'N/A',
                f"{animal.peso:.2f}" if animal.peso else 'N/A',
                animal.estado or 'N/A',
                animal.fecha_ingreso.strftime('%d/%m/%Y') if animal.fecha_ingreso else 'N/A',
                animal.fecha_venta.strftime('%d/%m/%Y') if animal.fecha_venta else 'N/A',
                animal.comprador or 'N/A'
            ])
        
        # Crear tabla con estilos
        col_widths = [
            doc.width * 0.08,  # ID
            doc.width * 0.12,  # Nombre
            doc.width * 0.1,   # Tipo
            doc.width * 0.12,  # Raza
            doc.width * 0.06,  # Sexo
            doc.width * 0.1,   # Fecha Nac.
            doc.width * 0.07,  # Edad
            doc.width * 0.08,  # Peso
            doc.width * 0.1,   # Estado
            doc.width * 0.1,   # Ingreso
            doc.width * 0.1,   # Fecha Venta
            doc.width * 0.1,   # Comprador
        ]
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Estilo de la tabla
        table_style = TableStyle([
            # Estilo del encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 5),
            
            # Estilo de las celdas de datos
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2d3748')),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            
            # Alternar colores de filas para mejor legibilidad
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
            
            # Ajustar alineación de columnas específicas
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # ID
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),    # Nombre
            ('ALIGN', (4, 0), (4, -1), 'CENTER'),  # Sexo
            ('ALIGN', (6, 0), (7, -1), 'CENTER'),  # Edad y Peso
        ])
        
        # Aplicar estilos a la tabla
        table.setStyle(table_style)
        
        # Agregar la tabla al documento
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Pie de página
        elements.append(Paragraph("Generado por AgroGest - Sistema de Gestión Ganadera", 
                               ParagraphStyle('Footer', 
                                            parent=styles['Normal'],
                                            fontSize=8,
                                            textColor=colors.HexColor('#6b7280'),
                                            alignment=TA_CENTER)))
        
        # Construir el PDF
        doc.build(elements)
        buffer.seek(0)
        
        # Preparar respuesta
        response = app.response_class(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=reporte_animales_{finca_nombre}_{datetime.now().strftime("%Y%m%d")}.pdf'
            }
        )
        
        return response
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generando reporte PDF de animales: {error_details}")
        flash(f'Error al generar el reporte PDF de animales: {str(e)}', 'error')
        return redirect(url_for('animales'))

@app.route('/exportar/inventario')
@login_required
def exportar_inventario():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    inventarios = Inventario.query.filter_by(finca_id=session['finca_id']).all()
    df = pd.DataFrame([{k: getattr(i, k) for k in ['id','producto','cantidad','unidad','precio_unitario','fecha_ingreso','fecha_vencimiento','categoria','tipo_animal']} for i in inventarios])
    return df.to_excel('inventario.xlsx', index=False), 200, {'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Content-Disposition': 'attachment; filename=inventario.xlsx'}

# --- CRUD Centros de Costo, Gastos e Ingresos ---
@app.route('/centros', methods=['GET', 'POST'])
@login_required
def centros_costo():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    if request.method == 'POST':
        centro = CentroCosto(
            nombre=request.form['nombre'],
            descripcion=request.form.get('descripcion'),
            finca_id=session['finca_id']
        )
        db.session.add(centro)
        db.session.commit()
        flash('Centro de costo creado', 'success')
        return redirect(url_for('centros_costo'))
    centros = CentroCosto.query.filter_by(finca_id=session['finca_id']).order_by(CentroCosto.nombre).all()
    return render_template('centros.html', centros=centros)

@app.route('/centros/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_centro(id):
    centro = CentroCosto.query.get_or_404(id)
    if centro.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('centros_costo'))
    db.session.delete(centro)
    db.session.commit()
    flash('Centro de costo eliminado', 'success')
    return redirect(url_for('centros_costo'))

@app.route('/gastos', methods=['GET', 'POST'])
@login_required
def gastos():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    if request.method == 'POST':
        gasto = Gasto(
            finca_id=session['finca_id'],
            centro_costo_id=parse_int(request.form.get('centro_costo_id')),
            categoria=request.form['categoria'],
            monto=float(request.form['monto']),
            fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
            descripcion=request.form.get('descripcion'),
            potrero_id=parse_int(request.form.get('potrero_id')),
            animal_id=parse_int(request.form.get('animal_id'))
        )
        db.session.add(gasto)
        db.session.commit()
        flash('Gasto registrado', 'success')
        return redirect(url_for('gastos'))
    centros = CentroCosto.query.filter_by(finca_id=session['finca_id']).all()
    potreros = Potrero.query.filter_by(finca_id=session['finca_id']).all()
    animales = Animal.query.filter_by(finca_id=session['finca_id']).filter(Animal.estado.in_(['activo'])).all()
    lista = Gasto.query.filter_by(finca_id=session['finca_id']).order_by(Gasto.fecha.desc()).all()
    return render_template('gastos.html', centros=centros, potreros=potreros, animales=animales, gastos=lista)

@app.route('/gastos/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_gasto(id):
    gasto = Gasto.query.get_or_404(id)
    if gasto.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('gastos'))
    db.session.delete(gasto)
    db.session.commit()
    flash('Gasto eliminado', 'success')
    return redirect(url_for('gastos'))

@app.route('/ingresos', methods=['GET', 'POST'])
@login_required
def ingresos():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    if request.method == 'POST':
        ingreso = Ingreso(
            finca_id=session['finca_id'],
            concepto=request.form['concepto'],
            monto=float(request.form['monto']),
            fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
            descripcion=request.form.get('descripcion')
        )
        db.session.add(ingreso)
        db.session.commit()
        flash('Ingreso registrado', 'success')
        return redirect(url_for('ingresos'))
    lista = Ingreso.query.filter_by(finca_id=session['finca_id']).order_by(Ingreso.fecha.desc()).all()
    return render_template('ingresos.html', ingresos=lista)

# Rutas para Animales
@app.route('/animales')
@login_required
def animales():
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    animales = Animal.query.filter_by(finca_id=session['finca_id']).all()
    potreros = Potrero.query.filter_by(finca_id=session['finca_id']).all()
    return render_template('animales.html', animales=animales, potreros=potreros, today=date.today())

# Rutas para Eventos

# API Endpoints para resúmenes del dashboard
@app.route('/api/resumen/animales')
@login_required
def api_resumen_animales():
    try:
        if 'finca_id' not in session:
            return jsonify({'error': 'No hay finca seleccionada'}), 400
        
        finca_id = session['finca_id']
        
        # Total de animales (con límite para evitar sobrecargas)
        total = Animal.query.filter_by(finca_id=finca_id).count()
        
        # Animales activos
        activos = Animal.query.filter_by(finca_id=finca_id, estado='activo').count()
        
        # Tipos únicos (de todos los animales excepto inactivos)
        tipos = db.session.query(Animal.tipo).filter(
            Animal.finca_id == finca_id,
            db.or_(
                Animal.estado.is_(None),
                Animal.estado == '',
                ~Animal.estado.in_(['inactivo', 'vendido', 'muerto', 'fallecido', 'dado_de_baja'])
            )
        ).distinct().count()
        
        # Por tipo (incluye todos excepto inactivos/vendidos/muertos/fallecidos)
        # Normalizamos Animal.tipo a lower() para consolidar entradas como 'Vaca' y 'vaca'
        por_tipo_rows = db.session.query(
            db.func.lower(Animal.tipo).label('tipo_norm'),
            db.func.count(Animal.id).label('cantidad')
        ).filter(
            Animal.finca_id == finca_id,
            db.or_(
                Animal.estado.is_(None),
                Animal.estado == '',
                ~Animal.estado.in_(['inactivo', 'vendido', 'muerto', 'fallecido', 'dado_de_baja'])
            )
        ).group_by(db.func.lower(Animal.tipo)).order_by(db.desc('cantidad')).limit(20).all()

        # Construir lista por_tipo con la primera letra en mayúscula para mostrar
        por_tipo = [{'tipo': (row.tipo_norm.title() if row.tipo_norm else 'Sin especificar'), 'cantidad': row.cantidad} for row in por_tipo_rows]

        # Tipos únicos (sobre activos, normalizados)
        tipos_unicos = [row['tipo'] for row in por_tipo]

        # Por raza (incluye todos excepto inactivos/vendidos/muertos)
        por_raza_rows = db.session.query(
            db.func.lower(Animal.raza).label('raza_norm'),
            db.func.count(Animal.id).label('cantidad')
        ).filter(
            Animal.finca_id == finca_id,
            db.or_(
                Animal.estado.is_(None),
                Animal.estado == '',
                ~Animal.estado.in_(['inactivo', 'vendido', 'muerto', 'fallecido', 'dado_de_baja'])
            )
        ).group_by(db.func.lower(Animal.raza)).order_by(db.desc('cantidad')).limit(20).all()

        por_raza = [{'raza': (row.raza_norm.title() if row.raza_norm else 'Sin especificar'), 'cantidad': row.cantidad} for row in por_raza_rows]
        razas_unicas = len([r for r in por_raza if r['raza'] != 'Sin especificar'])

        # Calcular promedio de edad (solo activos)
        hoy = date.today()
        animales_activos = Animal.query.filter_by(finca_id=finca_id, estado='activo').all()
        edades = []
        for animal in animales_activos:
            if animal.fecha_nacimiento:
                edad = (hoy - animal.fecha_nacimiento).days / 365.25
                edades.append(edad)
        promedio_edad = round(sum(edades) / len(edades), 1) if edades else 0

        # Identificar top tipo (el más frecuente)
        top_tipo = por_tipo[0]['tipo'] if por_tipo else None

        # Backwards-compatible response: include keys expected by existing dashboard JS
        return jsonify({
            'total': total,                      # total de registros en la finca (incluye inactivos)
            'total_animales': activos,           # (compat) cantidad de animales activos
            'activos': activos,
            'promedio_edad': promedio_edad,
            'tipos': tipos,
            'tipos_unicos': tipos_unicos,
            'top_tipo': top_tipo,
            'por_tipo': por_tipo,
            'razas_unicas': razas_unicas,
            'por_raza': por_raza
        })
    except Exception as e:
        print(f"[ERROR] En api_resumen_animales: {e}")
        return jsonify({'error': 'Error interno al cargar resumen de animales'}), 500

@app.route('/api/resumen/potreros')
@login_required
def api_resumen_potreros():
    try:
        if 'finca_id' not in session:
            return jsonify({'error': 'No hay finca seleccionada'}), 400
        
        finca_id = session['finca_id']
        
        # Total de potreros
        total = Potrero.query.filter_by(finca_id=finca_id).count()
        
        # Área total (con manejo de None)
        area_total = db.session.query(db.func.sum(Potrero.area)).filter_by(finca_id=finca_id).scalar() or 0
        
        # Potreros con información de ocupación (limitado)
        potreros = Potrero.query.filter_by(finca_id=finca_id).limit(50).all()
        potreros_data = []
        total_ocupacion = 0
        
        for p in potreros:
            animales = Animal.query.filter_by(potrero_id=p.id).count()
            ocupacion = (animales / p.capacidad * 100) if p.capacidad > 0 else 0
            total_ocupacion += ocupacion
            
            potreros_data.append({
                'nombre': p.nombre,
                'animales': animales,
                'capacidad': p.capacidad,
                'ocupacion': round(ocupacion, 1)
            })
        
        ocupacion_promedio = total_ocupacion / len(potreros) if potreros else 0
        
        return jsonify({
            'total': total,
            'area_total': float(area_total),
            'ocupacion_promedio': round(ocupacion_promedio, 1),
            'potreros': potreros_data
        })
    except Exception as e:
        print(f"[ERROR] En api_resumen_potreros: {e}")
        return jsonify({'error': 'Error interno al cargar resumen de potreros'}), 500

@app.route('/api/resumen/empleados')
@login_required
def api_resumen_empleados():
    try:
        if 'finca_id' not in session:
            return jsonify({'error': 'No hay finca seleccionada'}), 400
        
        finca_id = session['finca_id']
        
        # Total de empleados
        total = Empleado.query.filter_by(finca_id=finca_id).count()
        
        # Empleados activos
        activos = Empleado.query.filter_by(finca_id=finca_id, estado='activo').count()
        
        # Por cargo (limitado)
        por_cargo = db.session.query(
            Empleado.cargo,
            db.func.count(Empleado.id).label('cantidad')
        ).filter_by(finca_id=finca_id).group_by(Empleado.cargo).limit(10).all()
        
        return jsonify({
            'total': total,
            'activos': activos,
            'por_cargo': [{'cargo': c.cargo.title(), 'cantidad': c.cantidad} for c in por_cargo]
        })
    except Exception as e:
        print(f"[ERROR] En api_resumen_empleados: {e}")
        return jsonify({'error': 'Error interno al cargar resumen de empleados'}), 500

@app.route('/api/resumen/inventario')
@login_required
def api_resumen_inventario():
    try:
        if 'finca_id' not in session:
            return jsonify({'error': 'No hay finca seleccionada'}), 400
        
        finca_id = session['finca_id']
        
        # Total de items
        total_items = Inventario.query.filter_by(finca_id=finca_id).count()
        
        # Valor total (con manejo de None)
        valor_total = db.session.query(
            db.func.sum(Inventario.cantidad * Inventario.precio_unitario)
        ).filter_by(finca_id=finca_id).scalar() or 0
        
        # Items con bajo stock (limitado para eficiencia)
        bajo_stock = Inventario.query.filter(
            Inventario.finca_id == finca_id,
            Inventario.cantidad <= 10  # Umbral fijo de 10 unidades
        ).count()
        
        # Por categoría (limitado)
        por_categoria = db.session.query(
            Inventario.categoria,
            db.func.count(Inventario.id).label('items'),
            db.func.sum(Inventario.cantidad * Inventario.precio_unitario).label('valor')
        ).filter_by(finca_id=finca_id).group_by(Inventario.categoria).limit(10).all()
        
        return jsonify({
            'total_items': total_items,
            'valor_total': float(valor_total),
            'bajo_stock': bajo_stock,
            'por_categoria': [
                {
                    'categoria': c.categoria.title(),
                    'items': c.items,
                    'valor': float(c.valor or 0)
                } for c in por_categoria
            ]
        })
    except Exception as e:
        print(f"[ERROR] En api_resumen_inventario: {e}")
        return jsonify({'error': 'Error interno al cargar resumen de inventario'}), 500

# Rutas para Fincas
@app.route('/fincas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_finca():
    """Página para crear una nueva finca"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        extension = request.form.get('extension')
        tipo_produccion = request.form.get('tipo_produccion')
        propietario = request.form.get('propietario')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        descripcion = request.form.get('descripcion')
        ubicacion = request.form.get('ubicacion')
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        polygon_geojson = request.form.get('polygon_geojson')
        
        try:
            # Crear una nueva finca
            nueva_finca = Finca(
                nombre=nombre,
                direccion=direccion,
                extension=extension,
                tipo_produccion=tipo_produccion,
                propietario=propietario,
                telefono=telefono,
                email=email,
                descripcion=descripcion,
                ubicacion=ubicacion,
                latitud=lat,
                longitud=lng,
                poligono_geojson=polygon_geojson,
                usuario_id=session['user_id']
            )
            
            db.session.add(nueva_finca)
            db.session.commit()
            
            flash('Finca creada exitosamente', 'success')
            return redirect(url_for('fincas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la finca: {str(e)}', 'error')
    
    return render_template('nueva_finca.html')

@app.route('/fincas/editar/<int:finca_id>', methods=['GET', 'POST'])
@login_required
def editar_finca(finca_id):
    """Página para editar una finca existente"""
    finca = Finca.query.get_or_404(finca_id)
    
    # Verificar que la finca pertenezca al usuario
    if finca.usuario_id != session['user_id']:
        flash('Acción no autorizada', 'danger')
        return redirect(url_for('fincas'))
    
    if request.method == 'POST':
        finca.nombre = request.form.get('nombre')
        finca.direccion = request.form.get('direccion')
        finca.extension = request.form.get('extension')
        finca.tipo_produccion = request.form.get('tipo_produccion')
        finca.propietario = request.form.get('propietario')
        finca.telefono = request.form.get('telefono')
        finca.email = request.form.get('email')
        finca.descripcion = request.form.get('descripcion')
        finca.ubicacion = request.form.get('ubicacion')
        finca.latitud = request.form.get('lat')
        finca.longitud = request.form.get('lng')
        finca.poligono_geojson = request.form.get('polygon_geojson')
        
        try:
            db.session.commit()
            flash('Finca actualizada exitosamente', 'success')
            return redirect(url_for('fincas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la finca: {str(e)}', 'error')
    
    return render_template('editar_finca.html', finca=finca)

@app.route('/fincas', methods=['GET', 'POST'])
@login_required
def fincas():
    user_id = session['user_id']
    
    # Obtener el ID de la finca seleccionada de la sesión
    finca_seleccionada_id = session.get('finca_id')
    
    # Obtener todas las fincas del usuario
    fincas = Finca.query.filter_by(usuario_id=user_id).all()
    
    # Si no hay finca seleccionada y hay al menos una finca, seleccionar la primera
    if not finca_seleccionada_id and fincas:
        finca_seleccionada_id = fincas[0].id
        session['finca_id'] = finca_seleccionada_id
    
    # Obtener la finca seleccionada
    finca_seleccionada = None
    if finca_seleccionada_id:
        finca_seleccionada = Finca.query.get(finca_seleccionada_id)
    
    # Verificar que la finca seleccionada pertenezca al usuario
    if finca_seleccionada and finca_seleccionada.usuario_id != user_id:
        session.pop('finca_id', None)
        finca_seleccionada = None
    
    # Calcular el total de hectáreas
    total_hectareas = sum(f.extension or 0 for f in fincas)
    
    # Si es una solicitud POST, manejar la creación de una nueva finca
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        extension = request.form.get('extension')
        tipo_produccion = request.form.get('tipo_produccion')
        propietario = request.form.get('propietario')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        fecha_fundacion = request.form.get('fecha_fundacion')
        descripcion = request.form.get('descripcion')
        ubicacion = request.form.get('ubicacion')
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        polygon_geojson = request.form.get('polygon_geojson')
        
        try:
            # Crear una nueva finca
            nueva_finca = Finca(
                nombre=nombre,
                direccion=direccion,
                extension=float(extension) if extension else None,
                tipo_produccion=tipo_produccion,
                propietario=propietario,
                telefono=telefono,
                email=email,
                fecha_fundacion=datetime.strptime(fecha_fundacion, '%Y-%m-%d').date() if fecha_fundacion else None,
                descripcion=descripcion,
                ubicacion=ubicacion,
                latitud=float(lat) if lat else None,
                longitud=float(lng) if lng else None,
                poligono_geojson=polygon_geojson,
                usuario_id=user_id
            )
            
            db.session.add(nueva_finca)
            db.session.commit()
            
            # Si es la primera finca, establecerla como seleccionada
            if not finca_seleccionada:
                session['finca_id'] = nueva_finca.id
                finca_seleccionada = nueva_finca
            
            flash('Finca creada exitosamente', 'success')
            return redirect(url_for('fincas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la finca: {str(e)}', 'danger')
    
    # Renderizar la plantilla con las fincas y la finca seleccionada
    
    return render_template('fincas.html', 
                         fincas=fincas, 
                         finca_seleccionada=finca_seleccionada,
                         total_hectareas=total_hectareas)

@app.route('/finca/eliminar/<int:finca_id>', methods=['GET', 'POST'])
@login_required
def eliminar_finca(finca_id):
    # Verificar que el usuario sea admin
    if current_user.rol != 'admin':
        flash('No tienes permisos para eliminar fincas', 'error')
        return redirect(url_for('fincas'))
    
    finca = Finca.query.get_or_404(finca_id)
    
    if request.method == 'POST':
        try:
            # Verificar si hay animales asociados a esta finca
            animales_count = Animal.query.filter_by(finca_id=finca_id).count()
            if animales_count > 0:
                flash(f'No se puede eliminar la finca porque tiene {animales_count} animales asociados', 'error')
                return redirect(url_for('fincas'))
            
            # Eliminar todos los registros asociados a esta finca
            # Empleados
            Empleado.query.filter_by(finca_id=finca_id).delete()
            
            # Potreros
            potreros = Potrero.query.filter_by(finca_id=finca_id).all()
            for potrero in potreros:
                # Ubicaciones dentro de potreros
                Ubicacion.query.filter_by(potrero_id=potrero.id).delete()
            Potrero.query.filter_by(finca_id=finca_id).delete()
            
            # Inventario
            Inventario.query.filter_by(finca_id=finca_id).delete()
            
            # Centros de costo
            CentroCosto.query.filter_by(finca_id=finca_id).delete()
            
            # Gastos
            Gasto.query.filter_by(finca_id=finca_id).delete()
            
            # Vacunas
            Vacuna.query.filter_by(finca_id=finca_id).delete()
            
            # Finalmente eliminar la finca
            db.session.delete(finca)
            db.session.commit()
            
            flash('Finca eliminada exitosamente', 'success')
            return redirect(url_for('fincas'))
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Error al eliminar finca: {e}")
            flash('Error al eliminar la finca. Inténtalo de nuevo.', 'error')
            return redirect(url_for('fincas'))
    
    return render_template('eliminar_finca.html', finca=finca)

@app.route('/finca/seleccionar/<int:finca_id>')
@login_required
def seleccionar_finca(finca_id):
    finca = Finca.query.get_or_404(finca_id)
    session['finca_id'] = finca.id
    flash(f'Seleccionaste la finca: {finca.nombre}', 'success')
    return redirect(url_for('index'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

@app.context_processor
def inject_finca_model():
    return dict(Finca=Finca)

@app.route('/presentacion')
def presentacion():
    return render_template('presentacion.html')

@app.route('/agregar_dr_garcia')
@login_required
def agregar_dr_garcia():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Selecciona una finca para continuar', 'warning')
        return redirect(url_for('empleados'))
    from datetime import date
    # Importación absoluta para evitar ImportError
    from app_simple import db, Empleado, Finca
    # Verificar si ya existe
    existente = Empleado.query.filter_by(cedula='11223344', finca_id=finca_id).first()
    if existente:
        flash('El Dr. García ya está registrado en esta finca.', 'info')
        return redirect(url_for('empleados'))
    dr = Empleado(
        cedula='11223344',
        nombre='Dr.',
        apellido='García',
        telefono='0416-5556677',
        direccion='Calle Veterinaria #10',
        cargo='Veterinario',
        fecha_contratacion=date(2021, 5, 10),
        salario=1200.0,
        finca_id=finca_id
    )
    db.session.add(dr)
    db.session.commit()
    flash('Dr. García agregado exitosamente como veterinario.', 'success')
    return redirect(url_for('empleados'))

@app.route('/animal/<int:animal_id>/eliminar', methods=['POST'])
@login_required
def eliminar_animal(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    if animal.finca_id != session.get('finca_id'):
        flash('Acción no autorizada.', 'danger')
        return redirect(url_for('animales'))
    
    try:
        # Eliminar registros relacionados manualmente
        # Vacunas
        Vacuna.query.filter_by(animal_id=animal_id).delete()
        
        # Producciones
        Produccion.query.filter_by(animal_id=animal_id).delete()
        
        # Registros de peso
        RegistroPeso.query.filter_by(animal_id=animal_id).delete()
        
        # Servicios reproductivos
        ServicioReproductivo.query.filter_by(animal_id=animal_id).delete()
        
        # Diagnósticos de preñez
        DiagnosticoPrenez.query.filter_by(animal_id=animal_id).delete()
        
        # Partos
        Parto.query.filter_by(animal_id=animal_id).delete()
        
        # Finalmente eliminar el animal
        db.session.delete(animal)
        db.session.commit()
        
        flash('Animal y todos sus registros eliminados exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Error al eliminar animal: {e}")
        flash('Error al eliminar el animal. Inténtalo de nuevo.', 'error')
    
    return redirect(url_for('animales'))

# === SISTEMA REPRODUCTIVO ===
@app.route('/reproductivo')
@login_required
def calendario_reproductivo():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debe seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    # Obtener animales hembras
    hembras = Animal.query.filter_by(finca_id=finca_id, sexo='hembra').filter(Animal.estado.in_(['activo'])).all()
    
    # Servicios recientes (últimos 30 días)
    fecha_limite = date.today() - timedelta(days=30)
    servicios_recientes = db.session.query(ServicioReproductivo, Animal)\
        .join(Animal)\
        .filter(Animal.finca_id == finca_id)\
        .filter(ServicioReproductivo.fecha >= fecha_limite)\
        .order_by(ServicioReproductivo.fecha.desc())\
        .all()
    
    # Diagnósticos pendientes (servicios sin diagnóstico después de 30 días)
    servicios_sin_diagnostico = db.session.query(ServicioReproductivo, Animal)\
        .join(Animal)\
        .outerjoin(DiagnosticoPrenez, 
                  (DiagnosticoPrenez.animal_id == ServicioReproductivo.animal_id) &
                  (DiagnosticoPrenez.fecha >= ServicioReproductivo.fecha))\
        .filter(Animal.finca_id == finca_id)\
        .filter(ServicioReproductivo.fecha <= date.today() - timedelta(days=30))\
        .filter(DiagnosticoPrenez.id == None)\
        .all()
    
    # Partos esperados (diagnósticos positivos + 280 días)
    partos_esperados = db.session.query(DiagnosticoPrenez, Animal)\
        .join(Animal)\
        .filter(Animal.finca_id == finca_id)\
        .filter(DiagnosticoPrenez.resultado == 'preñada')\
        .all()
    
    partos_proximos = []
    for diagnostico, animal in partos_esperados:
        fecha_parto = diagnostico.fecha + timedelta(days=280)
        if fecha_parto >= date.today():
            partos_proximos.append({
                'animal': animal,
                'fecha_parto': fecha_parto,
                'dias_restantes': (fecha_parto - date.today()).days
            })
    
    partos_proximos.sort(key=lambda x: x['fecha_parto'])
    
    return render_template('calendario_reproductivo.html',
                         hembras=hembras,
                         servicios_recientes=servicios_recientes,
                         servicios_sin_diagnostico=servicios_sin_diagnostico,
                         partos_proximos=partos_proximos)

@app.route('/reproductivo/servicio', methods=['GET', 'POST'])
@login_required
def nuevo_servicio():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debe seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        servicio = ServicioReproductivo(
            animal_id=request.form['animal_id'],
            fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
            tipo_servicio=request.form['tipo_servicio'],
            semental_nombre=request.form.get('semental_nombre'),
            responsable=request.form.get('responsable'),
            observaciones=request.form.get('observaciones')
        )
        db.session.add(servicio)
        db.session.commit()
        flash('Servicio reproductivo registrado exitosamente.', 'success')
        return redirect(url_for('calendario_reproductivo'))
    
    hembras = Animal.query.filter_by(finca_id=finca_id, sexo='hembra').filter(Animal.estado.in_(['activo'])).all()
    machos = Animal.query.filter_by(finca_id=finca_id, sexo='macho').filter(Animal.estado.in_(['activo'])).all()
    return render_template('nuevo_servicio.html', hembras=hembras, machos=machos)

@app.route('/reproductivo/diagnostico', methods=['GET', 'POST'])
@login_required
def nuevo_diagnostico():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debe seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        diagnostico = DiagnosticoPrenez(
            animal_id=request.form['animal_id'],
            fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
            resultado=request.form['resultado'],
            metodo=request.form.get('metodo'),
            semanas_gestacion=request.form.get('semanas_gestacion') or None,
            observaciones=request.form.get('observaciones')
        )
        db.session.add(diagnostico)
        db.session.commit()
        flash('Diagnóstico de preñez registrado exitosamente.', 'success')
        return redirect(url_for('calendario_reproductivo'))
    
    hembras = Animal.query.filter_by(finca_id=finca_id, sexo='hembra').filter(Animal.estado.in_(['activo'])).all()
    return render_template('nuevo_diagnostico.html', hembras=hembras)

@app.route('/reproductivo/parto', methods=['GET', 'POST'])
@login_required
def registrar_parto():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debe seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        parto = Parto(
            animal_id=request.form['animal_id'],
            fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
            crias_vivas=request.form.get('crias_vivas') or 0,
            crias_muertas=request.form.get('crias_muertas') or 0,
            peso_promedio_crias=request.form.get('peso_promedio_crias') or None,
            dificultades=request.form.get('dificultades'),
            observaciones=request.form.get('observaciones')
        )
        db.session.add(parto)
        db.session.commit()
        flash('Parto registrado exitosamente.', 'success')
        return redirect(url_for('calendario_reproductivo'))
    
    hembras = Animal.query.filter_by(finca_id=finca_id, sexo='hembra').filter(Animal.estado.in_(['activo'])).all()
    return render_template('nuevo_parto.html', hembras=hembras)

# === SISTEMA DE SALUD ===
@app.route('/salud')
@login_required
def gestion_salud():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debe seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    # Obtener todos los animales
    animales = Animal.query.filter_by(finca_id=finca_id).filter(Animal.estado.in_(['activo'])).all()
    
    # Eventos de salud recientes (últimos 30 días)
    fecha_limite = date.today() - timedelta(days=30)
    eventos_recientes = db.session.query(HistorialSalud, Animal)\
        .join(Animal)\
        .filter(Animal.finca_id == finca_id)\
        .filter(HistorialSalud.fecha_inicio >= fecha_limite)\
        .order_by(HistorialSalud.fecha_inicio.desc())\
        .all()
    
    # Tratamientos activos
    tratamientos_activos = db.session.query(HistorialSalud, Animal)\
        .join(Animal)\
        .filter(Animal.finca_id == finca_id)\
        .filter(HistorialSalud.fecha_fin == None)\
        .filter(HistorialSalud.tipo_evento.in_(['tratamiento', 'medicamento']))\
        .all()
    
    # Próximas vacunaciones (simulado - en una implementación real sería un calendario)
    proximas_vacunaciones = []
    
    # Estadísticas de salud
    total_eventos = db.session.query(HistorialSalud)\
        .join(Animal)\
        .filter(Animal.finca_id == finca_id)\
        .count()
    
    eventos_mes = db.session.query(HistorialSalud)\
        .join(Animal)\
        .filter(Animal.finca_id == finca_id)\
        .filter(HistorialSalud.fecha_inicio >= fecha_limite)\
        .count()
    
    return render_template('gestion_salud.html',
                         animales=animales,
                         eventos_recientes=eventos_recientes,
                         tratamientos_activos=tratamientos_activos,
                         proximas_vacunaciones=proximas_vacunaciones,
                         total_eventos=total_eventos,
                         eventos_mes=eventos_mes)

@app.route('/salud/evento', methods=['GET', 'POST'])
@login_required
def registrar_evento_salud():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debe seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        evento = HistorialSalud(
            animal_id=request.form['animal_id'],
            tipo_evento=request.form['tipo_evento'],
            descripcion=request.form['descripcion'],
            fecha_inicio=datetime.strptime(request.form['fecha_inicio'], '%Y-%m-%d').date(),
            fecha_fin=datetime.strptime(request.form['fecha_fin'], '%Y-%m-%d').date() if request.form.get('fecha_fin') else None,
            tratamiento=request.form.get('tratamiento'),
            dias_tratamiento=request.form.get('dias_tratamiento') or None,
            resultado=request.form.get('resultado'),
            observaciones=request.form.get('observaciones')
        )
        db.session.add(evento)
        db.session.commit()
        flash('Evento de salud registrado exitosamente.', 'success')
        return redirect(url_for('gestion_salud'))
    
    animales = Animal.query.filter_by(finca_id=finca_id).filter(Animal.estado.in_(['activo'])).all()
    return render_template('nuevo_evento_salud.html', animales=animales)

@app.route('/salud/vacunacion', methods=['GET', 'POST'])
@login_required
def nueva_vacunacion():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debe seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Crear evento de vacunación
        vacunacion = HistorialSalud(
            animal_id=request.form['animal_id'],
            tipo_evento='vacunacion',
            descripcion=f"Vacuna: {request.form['tipo_vacuna']}",
            fecha_inicio=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
            tratamiento=f"Vacuna {request.form['tipo_vacuna']} - Dosis: {request.form.get('dosis', 'N/A')}",
            resultado='aplicada',
            observaciones=request.form.get('observaciones')
        )
        db.session.add(vacunacion)
        db.session.commit()
        flash('Vacunación registrada exitosamente.', 'success')
        return redirect(url_for('gestion_salud'))
    
    animales = Animal.query.filter_by(finca_id=finca_id).filter(Animal.estado.in_(['activo'])).all()
    return render_template('nueva_vacunacion.html', animales=animales)

# ============================================================================
# SISTEMA DE SEGUIMIENTO DE PESO
# ============================================================================

@app.route('/camaras')
@login_required
def camaras():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debes seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    # Obtener todas las cámaras de la finca
    camaras = Camara.query.filter_by(finca_id=finca_id).order_by(Camara.posicion).all()
    return render_template('camara.html', cameras=camaras)

@app.route('/agregar_camara', methods=['POST'])
@login_required
def agregar_camara():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debes seleccionar una finca primero.', 'danger')
        return redirect(url_for('index'))
    
    nombre = request.form.get('nombre')
    url = request.form.get('url')
    
    if not nombre or not url:
        flash('Todos los campos son requeridos', 'danger')
        return redirect(url_for('camaras'))
    
    # Obtener la última posición
    ultima_posicion = db.session.query(db.func.max(Camara.posicion)).filter_by(finca_id=finca_id).scalar() or 0
    
    nueva_camara = Camara(
        nombre=nombre,
        url=url,
        finca_id=finca_id,
        posicion=ultima_posicion + 1
    )
    
    db.session.add(nueva_camara)
    db.session.commit()
    
    flash('Cámara agregada correctamente', 'success')
    return redirect(url_for('camaras'))

@app.route('/editar_camara/<int:id>', methods=['POST'])
@login_required
def editar_camara(id):
    camara = Camara.query.get_or_404(id)
    finca_id = session.get('finca_id')
    
    if not finca_id or camara.finca_id != finca_id:
        flash('No autorizado', 'danger')
        return redirect(url_for('index'))
    
    camara.nombre = request.form.get('nombre', camara.nombre)
    camara.url = request.form.get('url', camara.url)
    
    db.session.commit()
    flash('Cámara actualizada correctamente', 'success')
    return redirect(url_for('camaras'))

@app.route('/eliminar_camara/<int:id>', methods=['POST'])
@login_required
def eliminar_camara(id):
    camara = Camara.query.get_or_404(id)
    finca_id = session.get('finca_id')
    
    if not finca_id or camara.finca_id != finca_id:
        flash('No autorizado', 'danger')
        return redirect(url_for('index'))
    
    db.session.delete(camara)
    db.session.commit()
    
    flash('Cámara eliminada correctamente', 'success')
    return redirect(url_for('camaras'))

@app.route('/ver_camara/<int:id>')
@login_required
def ver_camara(id):
    camara = Camara.query.get_or_404(id)
    finca_id = session.get('finca_id')
    
    if not finca_id or camara.finca_id != finca_id:
        flash('No autorizado', 'danger')
        return redirect(url_for('index'))
    
    return render_template('ver_camara.html', camara=camara)

@app.route('/actualizar_orden_camaras', methods=['POST'])
@login_required
def actualizar_orden_camaras():
    data = request.get_json()
    finca_id = session.get('finca_id')
    
    if not finca_id:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        for item in data:
            camara = Camara.query.get(item['id'])
            if camara and camara.finca_id == finca_id:
                camara.posicion = item['posicion']
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/grabaciones')
@login_required
def grabaciones():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debes seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    # Obtener fecha de la consulta
    fecha_consulta = request.args.get('date')
    
    # Listar archivos de grabaciones
    import os
    recordings_dir = os.path.join('static', 'recordings')
    archivos = []
    if os.path.exists(recordings_dir):
        for archivo in os.listdir(recordings_dir):
            if archivo.endswith('.mp4'):
                fecha_archivo = os.path.splitext(archivo)[0]
                if fecha_consulta and fecha_archivo != fecha_consulta:
                    continue
                archivos.append({
                    'nombre': archivo,
                    'fecha': fecha_archivo
                })
        # Ordenar por fecha descendente
        archivos.sort(key=lambda x: x['fecha'], reverse=True)
    else:
        # Crear directorio si no existe (no destructivo)
        try:
            os.makedirs(recordings_dir, exist_ok=True)
        except Exception:
            pass
    
    return render_template('grabaciones.html', archivos=archivos, fecha_consulta=fecha_consulta)

class RegistroPeso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    peso = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    condicion_corporal = db.Column(db.Integer)  # Escala 1-9
    observaciones = db.Column(db.Text)
    
    # Relaciones
    animal = db.relationship('Animal', backref='registros_peso', lazy=True)

# SISTEMA DE ALERTAS MEJORADO
# ============================================================================

class AlertaPersonalizada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    finca_id = db.Column(db.Integer, db.ForeignKey('finca.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_programada = db.Column(db.DateTime, nullable=False)
    tipo_alerta = db.Column(db.String(50), nullable=False)  # general, animal, vacuna, produccion, empleado
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'))  # Opcional para alertas específicas de animales
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, enviada, cancelada
    enviada = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    repetir = db.Column(db.Boolean, default=False)
    frecuencia = db.Column(db.String(20))  # diaria, semanal, mensual
    
    # Relaciones
    usuario = db.relationship('Usuario', backref='alertas_personalizadas')
    finca = db.relationship('Finca', backref='alertas')
    animal = db.relationship('Animal', backref='alertas')

@app.route('/alertas')
@login_required
def alertas():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debes seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    alertas = AlertaPersonalizada.query.filter(
        AlertaPersonalizada.usuario_id == current_user.id,
        AlertaPersonalizada.finca_id == finca_id
    ).order_by(AlertaPersonalizada.fecha_programada.desc()).all()
    
    return render_template('alertas.html', alertas=alertas)

@app.route('/nueva_alerta', methods=['GET', 'POST'])
@login_required
def nueva_alerta():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debes seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Combinar fecha y hora
        fecha_str = request.form['fecha']
        hora_str = request.form['hora']
        fecha_programada = datetime.strptime(f"{fecha_str} {hora_str}", '%Y-%m-%d %H:%M')
        
        alerta = AlertaPersonalizada(
            usuario_id=current_user.id,
            finca_id=finca_id,
            titulo=request.form['titulo'],
            descripcion=request.form['descripcion'],
            fecha_programada=fecha_programada,
            tipo_alerta=request.form['tipo_alerta'],
            animal_id=request.form.get('animal_id') if request.form.get('animal_id') else None,
            repetir=bool(request.form.get('repetir')),
            frecuencia=request.form.get('frecuencia') if request.form.get('repetir') else None
        )
        
        db.session.add(alerta)
        db.session.commit()
        
        # Solo confirmamos en pantalla; el email se enviará cuando el scheduler detecte que llegó la fecha_programada
        flash('Alerta creada correctamente. Se enviará a la hora programada.', 'success')
        
        return redirect(url_for('alertas'))
    
    animales = Animal.query.filter_by(finca_id=finca_id).filter(Animal.estado.in_(['activo'])).all()
    return render_template('nueva_alerta.html', animales=animales)
@app.route('/editar_alerta/<int:alerta_id>', methods=['GET', 'POST'])
@login_required
def editar_alerta(alerta_id):
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debes seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    alerta = AlertaPersonalizada.query.filter_by(
        id=alerta_id, 
        usuario_id=current_user.id, 
        finca_id=finca_id
    ).first_or_404()
    
    if request.method == 'POST':
        # Combinar fecha y hora
        fecha_str = request.form['fecha']
        hora_str = request.form['hora']
        fecha_programada = datetime.strptime(f"{fecha_str} {hora_str}", '%Y-%m-%d %H:%M')
        
        # Actualizar alerta
        alerta.titulo = request.form['titulo']
        alerta.descripcion = request.form['descripcion']
        alerta.fecha_programada = fecha_programada
        alerta.tipo_alerta = request.form['tipo_alerta']
        alerta.animal_id = request.form.get('animal_id') if request.form.get('animal_id') else None
        alerta.repetir = bool(request.form.get('repetir'))
        alerta.frecuencia = request.form.get('frecuencia') if request.form.get('repetir') else None
        
        db.session.commit()
        flash('Alerta actualizada exitosamente.', 'success')
        return redirect(url_for('alertas'))
    
    animales = Animal.query.filter_by(finca_id=finca_id).filter(Animal.estado.in_(['activo'])).all()
    return render_template('editar_alerta.html', alerta=alerta, animales=animales)

@app.route('/test_email_alert')
@login_required
def test_email_alert():
    """Ruta de prueba para enviar una alerta de email al usuario admin"""
    try:
        # Crear alerta de prueba
        from datetime import datetime, timedelta
        
        # Buscar usuario admin
        admin_user = Usuario.query.filter_by(username='admin').first()
        if not admin_user:
            return f"Usuario admin no encontrado"
        
        # Obtener finca del admin
        finca = Finca.query.filter_by(usuario_id=admin_user.id).first()
        if not finca:
            return f"No se encontró finca para el usuario admin"
        
        # Crear alerta de prueba
        alerta_prueba = AlertaPersonalizada(
            usuario_id=admin_user.id,
            finca_id=finca.id,
            titulo="Alerta de Prueba - Sistema AgroGest",
            descripcion="Esta es una alerta de prueba para verificar que el sistema de notificaciones por email funciona correctamente.",
            fecha_programada=datetime.now() + timedelta(hours=1),
            tipo_alerta="general",
            animal_id=None,
            repetir=False,
            frecuencia=None
        )
        
        db.session.add(alerta_prueba)
        db.session.commit()
        
        # Enviar email
        print(f"[TEST] Enviando email de prueba a: {admin_user.email}")
        resultado = enviar_notificacion_email(admin_user, alerta_prueba)
        
        if resultado:
            return f"✅ Email de prueba enviado exitosamente a {admin_user.email}. Revisa tu bandeja de entrada."
        else:
            return f"❌ Error enviando email a {admin_user.email}. Revisa los logs del servidor."
            
    except Exception as e:
        import traceback
        return f"❌ Error en prueba de email: {str(e)}<br><pre>{traceback.format_exc()}</pre>"

def verificar_alertas_pendientes():
    """Función que verifica y envía alertas pendientes"""
    if not EMAIL_AVAILABLE:
        return
    
    try:
        with app.app_context():
            ahora = datetime.now()
            fecha_actual = ahora.date()
            hora_actual = ahora.time()
            
            # Buscar alertas que deben enviarse ahora (con margen de 2 minutos)
            margen_minutos = timedelta(minutes=2)
            hora_limite = (ahora + margen_minutos).time()
            
            alertas_pendientes = AlertaPersonalizada.query.filter(
                AlertaPersonalizada.fecha_programada <= ahora,
                AlertaPersonalizada.estado == 'pendiente'
            ).all()
            
            for alerta in alertas_pendientes:
                try:
                    # Obtener usuario y su email
                    usuario = db.session.get(Usuario, alerta.usuario_id)
                    if usuario and usuario.email:
                        resultado = enviar_notificacion_email(usuario, alerta)
                        if resultado:
                            alerta.estado = 'enviada'
                            db.session.commit()
                            print(f"[INFO] Alerta enviada: {alerta.titulo} a {usuario.email}")
                        else:
                            print(f"[ERROR] No se pudo enviar alerta: {alerta.titulo}")
                except Exception as e:
                    print(f"[ERROR] Error procesando alerta {alerta.id}: {str(e)}")
                    continue
                    
    except Exception as e:
        print(f"[ERROR] Error en verificar_alertas_pendientes: {str(e)}")

def iniciar_scheduler():
    """Inicia el scheduler de alertas"""
    if not SCHEDULER_AVAILABLE:
        print("[WARNING] Scheduler no disponible - alertas automáticas deshabilitadas")
        return None
        
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=verificar_alertas_pendientes,
        trigger=IntervalTrigger(seconds=60),  # Verificar cada minuto
        id='verificar_alertas',
        name='Verificar alertas pendientes',
        replace_existing=True
    )
    scheduler.start()
    
    # Asegurar que el scheduler se cierre al terminar la aplicación
    atexit.register(lambda: scheduler.shutdown())
    
    print("[INFO] Scheduler de alertas iniciado - verificando cada 60 segundos")
    return scheduler

@app.route('/cancelar_alerta/<int:alerta_id>', methods=['POST'])
@login_required
def cancelar_alerta(alerta_id):
    """Cancela una alerta específica"""
    try:
        finca_id = session.get('finca_id')
        if not finca_id:
            return jsonify({'success': False, 'error': 'No hay finca seleccionada'}), 400
        
        alerta = AlertaPersonalizada.query.filter_by(
            id=alerta_id, 
            usuario_id=current_user.id, 
            finca_id=finca_id
        ).first()
        
        if not alerta:
            return jsonify({'success': False, 'error': 'Alerta no encontrada'}), 404
        
        # Cambiar estado a cancelada
        alerta.estado = 'cancelada'
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Alerta cancelada correctamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/completar_alerta/<int:alerta_id>', methods=['POST'])
@login_required
def completar_alerta(alerta_id):
    """Marca una alerta como completada/enviada"""
    try:
        finca_id = session.get('finca_id')
        if not finca_id:
            return jsonify({'success': False, 'error': 'No hay finca seleccionada'}), 400
        
        alerta = AlertaPersonalizada.query.filter_by(
            id=alerta_id, 
            usuario_id=current_user.id, 
            finca_id=finca_id
        ).first()
        
        if not alerta:
            return jsonify({'success': False, 'error': 'Alerta no encontrada'}), 404
        
        # Cambiar estado a enviada (completada)
        alerta.estado = 'enviada'
        alerta.enviada = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Alerta marcada como completada'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/eliminar_alerta/<int:alerta_id>', methods=['POST'])
@login_required
def eliminar_alerta(alerta_id):
    """Elimina permanentemente una alerta específica"""
    try:
        finca_id = session.get('finca_id')
        if not finca_id:
            return jsonify({'success': False, 'error': 'No hay finca seleccionada'}), 400
        
        alerta = AlertaPersonalizada.query.filter_by(
            id=alerta_id, 
            usuario_id=current_user.id, 
            finca_id=finca_id
        ).first()
        
        if not alerta:
            return jsonify({'success': False, 'error': 'Alerta no encontrada'}), 404
        
        # Eliminar permanentemente de la base de datos
        db.session.delete(alerta)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Alerta eliminada permanentemente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerta_detalle/<int:alerta_id>')
@login_required
def api_alerta_detalle(alerta_id):
    """API para obtener detalles completos de una alerta"""
    finca_id = session.get('finca_id')
    if not finca_id:
        return jsonify({'error': 'No hay finca seleccionada'}), 400
    
    alerta = AlertaPersonalizada.query.filter_by(
        id=alerta_id, 
        usuario_id=current_user.id, 
        finca_id=finca_id
    ).first()
    
    if not alerta:
        return jsonify({'error': 'Alerta no encontrada'}), 404
    
    # Obtener información del animal si existe
    animal_info = None
    if alerta.animal_id:
        animal = Animal.query.get(alerta.animal_id)
        if animal:
            animal_info = {
                'identificacion': animal.identificacion,
                'nombre': animal.nombre or 'Sin nombre',
                'tipo': animal.tipo,
                'raza': animal.raza
            }
    
    return jsonify({
        'id': alerta.id,
        'titulo': alerta.titulo,
        'descripcion': alerta.descripcion,
        'tipo_alerta': alerta.tipo_alerta,
        'fecha_programada': alerta.fecha_programada.strftime('%d/%m/%Y %H:%M'),
        'estado': alerta.estado,
        'fecha_creacion': alerta.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
        'repetir': alerta.repetir,
        'frecuencia': alerta.frecuencia,
        'animal': animal_info
    })

# ============================================================================
# API PARA OBTENER ANIMALES EN UBICACIONES
# ============================================================================

@app.route('/api/animales_en_ubicacion')
@login_required
def api_animales_en_ubicacion():
    """API para obtener animales en una ubicación específica"""
    tipo = request.args.get('tipo')  # 'potrero' o 'ubicacion'
    ubicacion_id = request.args.get('id')
    
    if not tipo or not ubicacion_id:
        return jsonify({'error': 'Parámetros requeridos: tipo e id'}), 400
    
    finca_id = session.get('finca_id')
    if not finca_id:
        return jsonify({'error': 'No hay finca seleccionada'}), 400
    
    try:
        if tipo == 'potrero':
            animales = Animal.query.filter_by(
                finca_id=finca_id,
                potrero_id=int(ubicacion_id)
            ).all()
        elif tipo == 'ubicacion':
            animales = Animal.query.filter_by(
                finca_id=finca_id,
                ubicacion_id=int(ubicacion_id)
            ).all()
        else:
            return jsonify({'error': 'Tipo no válido'}), 400
        
        animales_data = []
        for animal in animales:
            animales_data.append({
                'id': animal.id,
                'identificacion': animal.identificacion,
                'nombre': animal.nombre,
                'tipo': animal.tipo,
                'raza': animal.raza,
                'peso': animal.peso,
                'estado': animal.estado,
                'sexo': animal.sexo
            })
        
        return jsonify({'animales': animales_data})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# SISTEMA DE SEGUIMIENTO DE PESO
# ============================================================================

@app.route('/peso')
@login_required
def seguimiento_peso():
    """Dashboard de seguimiento de peso"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para ver el seguimiento de peso')
        return redirect(url_for('fincas'))
    
    finca_id = session['finca_id']
    
    # Estadísticas básicas
    total_registros = db.session.query(func.count(RegistroPeso.id))\
        .join(Animal, RegistroPeso.animal_id == Animal.id)\
        .filter(Animal.finca_id == finca_id)\
        .scalar() or 0
    total_animales = db.session.query(func.count(func.distinct(Animal.id)))\
        .join(RegistroPeso, RegistroPeso.animal_id == Animal.id)\
        .filter(Animal.finca_id == finca_id)\
        .scalar() or 0
    
    # Peso promedio actual
    peso_promedio = db.session.query(func.avg(RegistroPeso.peso))\
        .join(Animal, RegistroPeso.animal_id == Animal.id)\
        .filter(Animal.finca_id == finca_id)\
        .scalar() or 0
    
    # Registros recientes (evitar cargar la entidad completa para no requerir columnas inexistentes)
    filas_recientes = db.session.query(
            RegistroPeso.id,
            RegistroPeso.animal_id,
            RegistroPeso.peso,
            RegistroPeso.fecha,
            RegistroPeso.condicion_corporal,
            RegistroPeso.observaciones,
            Animal.identificacion,
            Animal.nombre
        )\
        .join(Animal, RegistroPeso.animal_id == Animal.id)\
        .filter(Animal.finca_id == finca_id)\
        .order_by(RegistroPeso.fecha.desc())\
        .limit(10).all()

    # Adaptar a estructura esperada por la plantilla: (registro_like, identificacion, nombre)
    registros_recientes = []
    for fila in filas_recientes:
        (_id, _animal_id, peso, fecha, condicion_corporal, observaciones, identificacion, nombre) = fila
        registro_like = SimpleNamespace(
            id=_id,
            peso=peso,
            condicion_corporal=condicion_corporal,
            fecha=fecha,
            observaciones=observaciones
        )
        registros_recientes.append((registro_like, identificacion, nombre))
    
    stats = {
        'total_registros': total_registros,
        'total_animales': total_animales,
        'peso_promedio': round(peso_promedio, 2) if peso_promedio else 0,
        'registros_recientes': registros_recientes
    }
    
    return render_template('seguimiento_peso.html', stats=stats)

@app.route('/peso/reporte/pdf')
@login_required
def reporte_peso_pdf():
    """Genera un reporte PDF de historial de peso"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para continuar')
        return redirect(url_for('fincas'))
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib import colors
        from io import BytesIO
        
        finca_id = session['finca_id']
        
        # Obtener datos del reporte
        finca = Finca.query.get(finca_id)
        
        # Obtener todos los registros de peso con información del animal
        registros = db.session.query(
            RegistroPeso.id,
            RegistroPeso.peso,
            RegistroPeso.fecha,
            RegistroPeso.condicion_corporal,
            RegistroPeso.observaciones,
            Animal.id.label('animal_id'),
            Animal.identificacion,
            Animal.nombre,
            Animal.tipo,
            Animal.raza,
            Animal.fecha_nacimiento
        )\
        .join(Animal, RegistroPeso.animal_id == Animal.id)\
        .filter(Animal.finca_id == finca_id)\
        .order_by(Animal.identificacion, RegistroPeso.fecha.desc())\
        .all()
        
        # Agrupar registros por animal
        registros_por_animal = {}
        for registro in registros:
            animal_id = registro.animal_id
            if animal_id not in registros_por_animal:
                registros_por_animal[animal_id] = {
                    'identificacion': registro.identificacion,
                    'nombre': registro.nombre,
                    'tipo': registro.tipo,
                    'raza': registro.raza,
                    'fecha_nacimiento': registro.fecha_nacimiento,
                    'registros': []
                }
            
            registros_por_animal[animal_id]['registros'].append({
                'peso': registro.peso,
                'fecha': registro.fecha,
                'condicion_corporal': registro.condicion_corporal,
                'observaciones': registro.observaciones
            })
        
        # Estadísticas generales
        total_registros = len(registros)
        total_animales = len(registros_por_animal)
        peso_promedio_general = sum(r.peso for r in registros) / len(registros) if registros else 0
        
        # Crear el documento PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title=f'Reporte de Seguimiento de Peso - {finca.nombre}'
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilo para el título
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Estilo para subtítulos
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Contenido del PDF
        elements = []
        
        # Título principal
        elements.append(Paragraph(f'Reporte de Seguimiento de Peso - {finca.nombre}', title_style))
        elements.append(Paragraph(f'Generado el: {date.today().strftime("%d/%m/%Y")}', styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Resumen general
        elements.append(Paragraph('Resumen General', subtitle_style))
        
        resumen_data = [
            ['Total de animales monitoreados:', str(total_animales)],
            ['Total de registros de peso:', str(total_registros)],
            ['Peso promedio general:', f'{round(peso_promedio_general, 2)} kg']
        ]
        
        resumen_table = Table(resumen_data, colWidths=[doc.width/2.0]*2)
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.HexColor('#6c757d')),
        ]))
        
        elements.append(resumen_table)
        elements.append(Spacer(1, 20))
        
        # Detalle por animal
        for animal_id, datos_animal in registros_por_animal.items():
            elements.append(Paragraph(f'Animal: {datos_animal["identificacion"]} - {datos_animal["nombre"] or "Sin nombre"}', subtitle_style))
            
            # Información básica del animal
            info_animal = [
                ['Tipo:', datos_animal['tipo'] or 'No especificado'],
                ['Raza:', datos_animal['raza'] or 'No especificado'],
                ['Fecha de Nacimiento:', datos_animal['fecha_nacimiento'].strftime('%d/%m/%Y') if datos_animal['fecha_nacimiento'] else 'N/A'],
                ['Total de Registros:', str(len(datos_animal['registros']))]
            ]
            
            info_table = Table(info_animal, colWidths=[doc.width/3.0]*3)
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17a2b8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e3f2fd')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bbdefb')),
            ]))
            
            elements.append(info_table)
            elements.append(Spacer(1, 10))
            
            # Tabla de historial de peso
            headers = ['Fecha', 'Peso (kg)', 'Condición Corporal', 'Observaciones']
            data_peso = [headers]
            
            for registro in datos_animal['registros']:
                data_peso.append([
                    registro['fecha'].strftime('%d/%m/%Y'),
                    f"{registro['peso']:.2f}",
                    f"{registro['condicion_corporal'] or '-'}" if registro['condicion_corporal'] else '-',
                    (registro['observaciones'] or '-')[:50] + ('...' if registro['observaciones'] and len(registro['observaciones']) > 50 else '')
                ])
            
            # Calcular estadísticas del animal
            pesos = [r['peso'] for r in datos_animal['registros']]
            peso_inicial = pesos[-1] if pesos else 0  # El más antiguo
            peso_actual = pesos[0] if pesos else 0    # El más reciente
            ganancia = peso_actual - peso_inicial
            
            # Agregar fila de resumen al final
            data_peso.append([
                'RESUMEN',
                f'Peso inicial: {peso_inicial:.2f} kg',
                f'Peso actual: {peso_actual:.2f} kg',
                f'Ganancia: {ganancia:+.2f} kg'
            ])
            
            peso_table = Table(data_peso, colWidths=[doc.width*0.2, doc.width*0.2, doc.width*0.2, doc.width*0.4])
            peso_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-2, -1), colors.HexColor('#f8fff8')),
                ('FONTSIZE', (0, 1), (-2, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c3e6cb')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            # Resaltar fila de resumen
            peso_table.setStyle(TableStyle([
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fff3cd')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#856404')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            
            elements.append(peso_table)
            elements.append(Spacer(1, 20))
        
        # Generar el PDF
        doc.build(elements)
        buffer.seek(0)
        
        # Preparar respuesta
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=reporte_seguimiento_peso_{date.today().strftime("%Y%m%d")}.pdf'
        
        return response
        
    except Exception as e:
        print(f"Error generando reporte PDF de peso: {e}")
        flash('Error al generar el reporte PDF', 'error')
        return redirect(url_for('seguimiento_peso'))

@app.route('/peso/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_registro_peso():
    """Crear nuevo registro de peso"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para registrar peso')
        return redirect(url_for('fincas'))
    
    finca_id = session['finca_id']
    
    if request.method == 'POST':
        try:
            animal_id = request.form['animal_id']
            peso = float(request.form['peso'])
            fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            condicion_corporal = request.form.get('condicion_corporal', type=int)
            observaciones = request.form.get('observaciones', '')
            
            # Verificar que el animal pertenece a la finca
            animal = Animal.query.filter_by(id=animal_id, finca_id=finca_id).first()
            if not animal:
                flash('Animal no encontrado', 'error')
                return redirect(url_for('nuevo_registro_peso'))
            
            # Crear registro
            registro = RegistroPeso(
                animal_id=animal_id,
                peso=peso,
                fecha=fecha,
                condicion_corporal=condicion_corporal,
                observaciones=observaciones
            )
            
            db.session.add(registro)
            db.session.commit()
            
            flash('Registro de peso guardado exitosamente', 'success')
            return redirect(url_for('seguimiento_peso'))
            
        except ValueError as e:
            flash('Error en los datos ingresados', 'error')
        except Exception as e:
            flash('Error al guardar el registro', 'error')
            db.session.rollback()
    
    # Obtener animales de la finca
    # Corregido: ordenar por un campo existente (identificacion) en lugar de un campo inexistente (numero)
    animales = Animal.query.filter_by(finca_id=finca_id).filter(Animal.estado.in_(['activo'])).order_by(Animal.identificacion).all()
    
    return render_template('nuevo_registro_peso.html', animales=animales)

@app.route('/peso/<int:registro_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_registro_peso(registro_id):
    """Editar un registro de peso existente"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para editar registros', 'error')
        return redirect(url_for('fincas'))
    
    finca_id = session['finca_id']
    
    # Obtener el registro con su animal
    registro = db.session.query(RegistroPeso, Animal).join(Animal).filter(
        RegistroPeso.id == registro_id,
        Animal.finca_id == finca_id
    ).first()
    
    if not registro:
        flash('Registro no encontrado', 'error')
        return redirect(url_for('seguimiento_peso'))
    
    registro_peso, animal = registro
    
    if request.method == 'POST':
        try:
            registro_peso.peso = float(request.form['peso'])
            registro_peso.fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            registro_peso.condicion_corporal = request.form.get('condicion_corporal', type=int)
            registro_peso.observaciones = request.form.get('observaciones', '')
            
            db.session.commit()
            flash('Registro de peso actualizado exitosamente', 'success')
            return redirect(url_for('seguimiento_peso'))
            
        except ValueError as e:
            flash('Error en los datos ingresados', 'error')
        except Exception as e:
            flash('Error al actualizar el registro', 'error')
            db.session.rollback()
    
    # Obtener animales de la finca
    animales = Animal.query.filter_by(finca_id=finca_id).filter(Animal.estado.in_(['activo'])).order_by(Animal.identificacion).all()
    
    return render_template('editar_registro_peso.html', registro=registro_peso, animal=animal, animales=animales)

@app.route('/peso/<int:registro_id>/detalle')
@login_required
def detalle_registro_peso(registro_id):
    """Ver detalles de un registro de peso"""
    if 'finca_id' not in session:
        flash('Selecciona una finca para ver detalles', 'error')
        return redirect(url_for('fincas'))
    
    finca_id = session['finca_id']
    
    # Obtener el registro con su animal
    registro = db.session.query(RegistroPeso, Animal).join(Animal).filter(
        RegistroPeso.id == registro_id,
        Animal.finca_id == finca_id
    ).first()
    
    if not registro:
        flash('Registro no encontrado', 'error')
        return redirect(url_for('seguimiento_peso'))
    
    registro_peso, animal = registro
    
    return render_template('detalle_registro_peso.html', registro=registro_peso, animal=animal, dt=datetime)

@app.route('/peso/<int:registro_id>/eliminar', methods=['POST'])
@login_required
def eliminar_registro_peso(registro_id):
    """Eliminar un registro de peso"""
    if 'finca_id' not in session:
        return jsonify({'success': False, 'message': 'No hay finca seleccionada'}), 400
    
    finca_id = session['finca_id']
    
    try:
        # Verificar que el registro pertenezca a la finca
        registro = db.session.query(RegistroPeso).join(Animal).filter(
            RegistroPeso.id == registro_id,
            Animal.finca_id == finca_id
        ).first()
        
        if not registro:
            return jsonify({'success': False, 'message': 'Registro no encontrado'}), 404
        
        db.session.delete(registro)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Registro eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al eliminar el registro: {str(e)}'}), 500

# ============================================================================
# CONFIGURACIÓN DE FINCA MEJORADA
# ============================================================================

@app.route('/configuracion_finca')
@login_required
def configuracion_finca():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debes seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    finca = Finca.query.get_or_404(finca_id)
    return render_template('configuracion_finca.html', finca=finca)

@app.route('/api/perfil_usuario')
@login_required
def api_perfil_usuario():
    """API para obtener datos del perfil del usuario actual"""
    try:
        usuario = db.session.get(Usuario, current_user.id)
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({
            'username': usuario.username,
            'email': usuario.email,
            'telefono': usuario.telefono,
            'nombre': usuario.nombre,
            'apellido': usuario.apellido,
            'rol': usuario.rol
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/actualizar_perfil', methods=['POST'])
@login_required
def api_actualizar_perfil():
    """API para actualizar datos del perfil del usuario"""
    try:
        data = request.get_json()
        print(f"Datos recibidos: {data}")  # Debug
        
        usuario = db.session.get(Usuario, current_user.id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # Actualizar campos si están presentes en la petición
        if 'email' in data and data['email']:
            usuario.email = data['email']
        if 'telefono' in data and data['telefono']:
            usuario.telefono = data['telefono']
        if 'nombre' in data and data['nombre']:
            usuario.nombre = data['nombre']
        if 'apellido' in data and data['apellido']:
            usuario.apellido = data['apellido']
        
        print(f"Usuario antes de guardar: {usuario.nombre} {usuario.apellido}")  # Debug
        db.session.commit()
        print("Cambios guardados exitosamente")  # Debug
        
        return jsonify({'message': 'Perfil actualizado correctamente'})
    except Exception as e:
        print(f"Error en api_actualizar_perfil: {str(e)}")  # Debug
        import traceback
        traceback.print_exc()  # Debug
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/actualizar_finca', methods=['POST'])
@login_required
def actualizar_finca():
    finca_id = session.get('finca_id')
    if not finca_id:
        flash('Debes seleccionar una finca primero.', 'warning')
        return redirect(url_for('index'))
    
    finca = Finca.query.get_or_404(finca_id)
    
    finca.nombre = request.form['nombre']
    finca.direccion = request.form['direccion']
    finca.telefono = request.form['telefono']
    finca.email = request.form['email']
    finca.descripcion = request.form.get('descripcion')
    db.session.commit()
    flash('Configuración de finca actualizada exitosamente.', 'success')
    return redirect(url_for('configuracion_finca'))

# Ruta para Control de Partos - DESACTIVADA
# @app.route('/control_partos')
# @login_required
# def control_partos():
#     if 'finca_id' not in session:
#         flash('Por favor selecciona una finca primero', 'warning')
#         return redirect(url_for('index'))
#     
#     try:
#         finca_id = session['finca_id']
#         
#         # Obtener animales preñadas (estado = 'preñada')
#         animales_preniadas = db.session.query(Animal).filter(
#             Animal.finca_id == finca_id,
#             Animal.estado == 'preñada'
#         ).all()
#         
#         # Obtener animales que han parido recientemente (últimos 30 días)
#         hace_30_dias = datetime.now().date() - timedelta(days=30)
#         partos_recientes = db.session.query(Animal).filter(
#             Animal.finca_id == finca_id,
#             Animal.fecha_real_parto.isnot(None),
#             Animal.fecha_real_parto >= hace_30_dias
#         ).order_by(Animal.fecha_real_parto.desc()).all()
#         
#         # Obtener todos los partos del año
#         ano_actual = datetime.now().year
#         partos_ano = db.session.query(Animal).filter(
#             Animal.finca_id == finca_id,
#             Animal.fecha_real_parto.isnot(None),
#             extract('year', Animal.fecha_real_parto) == ano_actual
#         ).order_by(Animal.fecha_real_parto.desc()).all()
#         
#         print("[DEBUG] Intentando renderizar template control_partos.html...")
#         try:
#             return render_template('control_partos.html', 
#                                animales_preniadas=animales_preniadas,
#                                partos_recientes=partos_recientes,
#                                partos_ano=partos_ano)
#         except Exception as template_error:
#             print(f"[ERROR] Error al renderizar template: {str(template_error)}")
#             raise template_error
#         
#     except Exception as e:
#         print(f"[ERROR] Error en control_partos: {str(e)}")
#         flash('Error al cargar el control de partos', 'danger')
#         return redirect(url_for('index'))

# API para buscar ubicación de un animal específico
@app.route('/api/buscar_animal')
@login_required
def buscar_animal():
    if 'finca_id' not in session:
        return jsonify({'error': 'No hay finca seleccionada'}), 400
    
    try:
        termino = request.args.get('termino', '').strip()
        if not termino:
            return jsonify({'error': 'Proporciona un término de búsqueda'}), 400
        
        finca_id = session['finca_id']
        print(f"[DEBUG] Buscando animal: '{termino}' en finca_id: {finca_id}")
        
        # Buscar por identificación o nombre
        animal = db.session.query(Animal).filter(
            Animal.finca_id == finca_id,
            or_(
                Animal.identificacion.ilike(f'%{termino}%'),
                Animal.nombre.ilike(f'%{termino}%')
            )
        ).first()
        
        print(f"[DEBUG] Animal encontrado: {animal}")
        
        if animal:
            # Calcular edad
            edad = None
            if animal.fecha_nacimiento:
                from datetime import date
                hoy = date.today()
                edad_dias = (hoy - animal.fecha_nacimiento).days
                edad_anios = edad_dias // 365
                if edad_anios == 0:
                    edad = f"{edad_dias // 30} meses"
                else:
                    edad = f"{edad_anios} años"
            
            # Determinar qué mostrar como ubicación
            ubicacion_mostrar = ''
            if animal.estado in ['vendido', 'fallecido', 'muerto']:
                ubicacion_mostrar = animal.estado.upper()
            else:
                ubicacion_mostrar = animal.potrero.nombre if animal.potrero and hasattr(animal.potrero, 'nombre') else 'Sin asignar'
            
            return jsonify({
                'encontrado': True,
                'animal': {
                    'id': animal.id,
                    'identificacion': animal.identificacion,
                    'nombre': animal.nombre or 'Sin nombre',
                    'potrero': ubicacion_mostrar,
                    'estado': animal.estado or 'Desconocido',
                    'tipo': animal.tipo or 'No especificado',
                    'sexo': animal.sexo or 'N/A',
                    'fecha_ingreso': animal.fecha_ingreso.strftime('%d/%m/%Y') if animal.fecha_ingreso else '',
                    'edad': edad or 'N/A'
                }
            })
        else:
            return jsonify({'encontrado': False, 'mensaje': 'Animal no encontrado'})
            
    except Exception as e:
        print(f"[ERROR] Error en buscar_animal: {str(e)}")
        return jsonify({'error': 'Error en la búsqueda'}), 500

# API para obtener datos de partos
@app.route('/api/partos_data')
@login_required
def partos_data():
    if 'finca_id' not in session:
        return jsonify({'error': 'No hay finca seleccionada'}), 400
    
    try:
        finca_id = session['finca_id']
        
        # Obtener animales preñadas
        animales_preniadas = db.session.query(Animal).filter(
            Animal.finca_id == finca_id,
            Animal.estado == 'preñada'
        ).all()
        
        # Obtener animales que han parido recientemente (últimos 30 días)
        hace_30_dias = datetime.now().date() - timedelta(days=30)
        partos_recientes = db.session.query(Animal).filter(
            Animal.finca_id == finca_id,
            Animal.fecha_real_parto.isnot(None),
            Animal.fecha_real_parto >= hace_30_dias
        ).order_by(Animal.fecha_real_parto.desc()).all()
        
        # También buscar partos registrados en eventos de salud
        try:
            print(f"[DEBUG] Buscando partos en eventos de salud para finca_id: {finca_id}")
            partos_eventos = db.session.query(EventoSalud).join(Animal).filter(
                Animal.finca_id == finca_id,
                EventoSalud.tipo_evento == 'parto'
            ).order_by(EventoSalud.fecha_evento.desc()).limit(50).all()
            print(f"[DEBUG] Partos encontrados en eventos: {len(partos_eventos)}")
        except Exception as e:
            print(f"[ERROR] Error buscando partos en eventos: {str(e)}")
            partos_eventos = []
        
        # Agregar partos de eventos a la lista si no están ya incluidos
        ids_animales_partos = {animal.id for animal in partos_recientes}
        for evento in partos_eventos:
            if evento.animal_id and evento.animal_id not in ids_animales_partos:
                dias_desde_parto = (datetime.now().date() - evento.fecha_evento).days if evento.fecha_evento else 0
                partos_recientes.append({
                    'id': evento.animal_id,
                    'identificacion': evento.animal.identificacion if hasattr(evento, 'animal') and evento.animal else 'Desconocido',
                    'nombre': evento.animal.nombre if hasattr(evento, 'animal') and evento.animal else 'Desconocido',
                    'dias_desde_parto': dias_desde_parto,
                    'fecha_parto': evento.fecha_evento.strftime('%d/%m/%Y') if evento.fecha_evento else 'Sin fecha',
                    'crias_vivas': evento.crias_vivas if hasattr(evento, 'crias_vivas') else 0
                })
        
        # Convertir a formato JSON
        preniadas_data = []
        for animal in animales_preniadas:
            dias_para_parto = None
            if animal.fecha_estimada_parto:
                dias_para_parto = (animal.fecha_estimada_parto - datetime.now().date()).days
            
            preniadas_data.append({
                'id': animal.id,
                'identificacion': animal.identificacion,
                'nombre': animal.nombre,
                'dias_para_parto': dias_para_parto,
                'fecha_estimada': animal.fecha_estimada_parto.strftime('%d/%m/%Y') if animal.fecha_estimada_parto else None
            })
        
        partidos_data = []
        # Procesar partos de animales (objetos Animal)
        for animal in partos_recientes:
            if hasattr(animal, 'fecha_real_parto'):  # Es un objeto Animal
                dias_desde_parto = (datetime.now().date() - animal.fecha_real_parto).days
                partidos_data.append({
                    'id': animal.id,
                    'identificacion': animal.identificacion,
                    'nombre': animal.nombre,
                    'dias_desde_parto': dias_desde_parto,
                    'fecha_parto': animal.fecha_real_parto.strftime('%d/%m/%Y'),
                    'crias_vivas': animal.crias_nacidas_vivas
                })
        
        # Procesar partos de eventos (objetos dict)
        for evento in partos_recientes:
            if isinstance(evento, dict):  # Es un objeto dict de eventos
                fecha_evento = evento.get('fecha_evento')
                if isinstance(fecha_evento, str):
                    # Convertir string a date si es necesario
                    try:
                        fecha_evento = datetime.strptime(fecha_evento, '%d/%m/%Y').date()
                    except:
                        fecha_evento = None
                
                dias_desde_parto = (datetime.now().date() - fecha_evento).days if fecha_evento else 0
                partidos_data.append({
                    'id': evento.get('id'),
                    'identificacion': evento.get('identificacion', 'Desconocido'),
                    'nombre': evento.get('nombre', 'Desconocido'),
                    'dias_desde_parto': dias_desde_parto,
                    'fecha_parto': fecha_evento.strftime('%d/%m/%Y') if fecha_evento else evento.get('fecha_parto', 'Sin fecha'),
                    'crias_vivas': evento.get('crias_vivas', 0)
                })
        
        return jsonify({
            'preniadas': preniadas_data,
            'partidos': partidos_data
        })
        
    except Exception as e:
        print(f"[ERROR] Error en partos_data: {str(e)}")
        return jsonify({'error': 'Error al cargar datos de partos'}), 500

if __name__ == '__main__':
    try:
        # Crear tablas si no existen
        with app.app_context():
            db.create_all()
            
            # Crear usuario admin por defecto si no existe
            if not Usuario.query.filter_by(username='admin').first():
                print('[DEBUG] Creando usuario admin por defecto...')
                admin = Usuario(
                    username='admin',
                    email='admin@finca.com',
                    password_hash=generate_password_hash('admin123'),
                    nombre='Administrador',
                    apellido='Sistema',
                    telefono='3001234567',
                    direccion='Sistema',
                    rol='admin'
                )
                db.session.add(admin)
                db.session.commit()
                print('OK Usuario administrador creado:')
                print('   Usuario: admin')
                print('   Contraseña: admin123')

        # Para Render, usar el puerto proporcionado por la variable de entorno
        port = int(os.environ.get('PORT', 5000))
        print(f'[INFO] Iniciando servidor en puerto {port}')

        # Iniciar el scheduler de alertas
        scheduler = iniciar_scheduler()

        # Escuchar en todas las interfaces y mostrar todas las direcciones IP disponibles
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f'[INFO] Tu dirección IP local es: {local_ip}')
        print(f'[INFO] Puedes acceder desde otros dispositivos en: http://{local_ip}:{port}')
        print(f'[INFO] También puedes intentar: http://192.168.1.112:{port}')
        
        app.run(host='0.0.0.0', port=port, debug=False)

    except Exception as e:
        import traceback
        print('[ERROR] Excepción al iniciar la app:')
        traceback.print_exc()
