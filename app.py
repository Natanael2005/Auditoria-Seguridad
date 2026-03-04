# 1. Librerías estándar de Python
import os
import logging 

# 2. Librerías externas (Terceros)
from flask import Flask, request, render_template, redirect, url_for, session
from dotenv import load_dotenv

# 3. Tus propios módulos (El código que tú y Diego hicieron)
from modules.auditoria import registrar_log_app, obtener_logs_app, supabase
from modules.server_logs import configurar_server_logs

# Cargamos las variables de entorno (.env)
load_dotenv()

# Iniciamos la aplicación
app = Flask(__name__)

# Configuramos la llave secreta
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

# Apagamos el log ruidoso de Flask para dejar solo el nuestro
log_werkzeug = logging.getLogger('werkzeug')
log_werkzeug.setLevel(logging.ERROR)


# =====================================================================
# CONFIGURACIÓN DE LOGS DE SERVIDOR
# =====================================================================
server_logger = configurar_server_logs()


@app.after_request
def log_server_request(response):
    """Guarda automáticamente cada petición HTTP en el archivo de texto local."""
    
    # MÉTODO FRANCOTIRADOR: Buscar la IP real en los headers, si no está, usar la normal
    ip_real = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

    server_logger.info(
        "Peticion web",
        extra={
            "clientip": ip_real,
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
        },
    )
    return response


# =====================================================================
# RUTAS DE LA APLICACIÓN
# =====================================================================
CORREO_ADMIN = "felipenatael33@gmail.com"

@app.route("/", methods=["GET", "POST"])
def login():
    if "usuario_actual" in session:
        if session["usuario_actual"] == CORREO_ADMIN:
            return redirect(url_for("vista_logs"))
        return redirect(url_for("dashboard"))

    error_msg = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        # Captura la IP real para el App Log
        ip_del_usuario = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

        try:
            auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            session["usuario_actual"] = auth_response.user.email

            registrar_log_app(usuario=email, accion="Login Exitoso", objetivo="Portal Leona Corp", estatus_http=200, ip_cliente=ip_del_usuario, detalles="Autenticación correcta.")
            
            # MAGIA: Redirección dependiendo de quién es
            if email == CORREO_ADMIN:
                return redirect(url_for("vista_logs"))
            else:
                return redirect(url_for("dashboard"))
                
        except Exception as e:
            error_msg = "Credenciales incorrectas. Intenta de nuevo."
            registrar_log_app(usuario=email, accion="Intento de Login Fallido", objetivo="Portal Leona Corp", estatus_http=401, ip_cliente=ip_del_usuario, detalles=f"Fallo: {str(e)}")

    return render_template("login.html", error=error_msg)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Ruta para crear cuentas falsas para la auditoría"""
    error_msg = None
    success_msg = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        # Captura la IP real para el App Log
        ip_del_usuario = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

        try:
            auth_response = supabase.auth.sign_up({"email": email, "password": password})
            success_msg = "Empleado registrado exitosamente. Ya puedes iniciar sesión."
            registrar_log_app(usuario=email, accion="Registro Nuevo Empleado", objetivo="Sistema Auth", estatus_http=200, ip_cliente=ip_del_usuario, detalles="Cuenta creada en Supabase.")
        except Exception as e:
            error_msg = f"Error al registrar: {str(e)}"
            registrar_log_app(usuario=email, accion="Fallo en Registro", objetivo="Sistema Auth", estatus_http=400, ip_cliente=ip_del_usuario, detalles=str(e))

    return render_template("register.html", error=error_msg, success=success_msg)

@app.route("/dashboard")
def dashboard():
    """El Portal Falso de Leona Corporation"""
    if "usuario_actual" not in session:
        return redirect(url_for("login"))
    
    # Solo renderizamos el portal, sin escaneos
    return render_template("dashboard.html", usuario=session["usuario_actual"])

@app.route("/accion_empleado", methods=["POST"])
def accion_empleado():
    if "usuario_actual" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario_actual"]
    tipo_accion = request.form.get("accion")
    
    # Captura la IP real para el App Log
    ip_del_usuario = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

    if tipo_accion == "nomina":
        detalles, estatus, msj = "Visualizó recibo de nómina.", 200, "Descargando recibo de nómina..."
    elif tipo_accion == "directorio":
        detalles, estatus, msj = "Accedió al directorio de empleados.", 200, "Abriendo directorio..."
    elif tipo_accion == "mensajes":
        detalles, estatus, msj = "Revisó bandeja de entrada.", 200, "No tienes mensajes nuevos."
    elif tipo_accion == "finanzas":
        detalles, estatus, msj = "ALERTA: Intento de acceso a DB Financiera.", 403, "Error 403: Permisos insuficientes."
    else:
        detalles, estatus, msj = "Acción desconocida.", 400, "Acción no válida."

    registrar_log_app(usuario=usuario, accion=f"Módulo: {tipo_accion}", objetivo="Datos Internos", estatus_http=estatus, ip_cliente=ip_del_usuario, detalles=detalles)
    return render_template("dashboard.html", usuario=usuario, mensaje=msj)

@app.route("/admin_financiero")
def ruta_finanzas():
    """Ruta oculta de alta sensibilidad"""
    usuario = session.get("usuario_actual", "Anonimo")
    ip_real = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    registrar_log_app(
        usuario=usuario, 
        accion="Acceso a Ruta Oculta", 
        objetivo="Finanzas_Direct", 
        estatus_http=403, 
        ip_cliente=ip_real, 
        detalles="ALERTA: Intento de acceso directo a base de datos financiera."
    )
    # Mostramos un error 403 real para la auditoría
    return "<h1>403 Forbidden</h1><p>No tienes permisos para estar aquí. Tu IP ha sido registrada.</p>", 403

@app.route("/cctv_interno")
def ruta_cctv():
    """Ruta oculta de cámaras"""
    usuario = session.get("usuario_actual", "Anonimo")
    ip_real = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    registrar_log_app(
        usuario=usuario, 
        accion="Acceso a Ruta Oculta", 
        objetivo="CCTV_Stream", 
        estatus_http=403, 
        ip_cliente=ip_real, 
        detalles="ALERTA: Intento de visualización de cámaras sin privilegios."
    )
    return "<h1>Acceso Denegado</h1><p>Esta es una red restringida de Leona Corp.</p>", 403

@app.route("/logs")
def vista_logs():
    if "usuario_actual" not in session:
        return redirect(url_for("login"))
    logs_recientes = obtener_logs_app(50)
    return render_template("logs.html", usuario=session["usuario_actual"], logs=logs_recientes)

@app.route("/logout")
def logout():
    if "usuario_actual" in session:
        ip_real = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        registrar_log_app(usuario=session["usuario_actual"], accion="Logout", objetivo="Portal Leona Corp", estatus_http=200, ip_cliente=ip_real, detalles="Sesión cerrada.")
        session.pop("usuario_actual", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"✅ [Sistema] Servidor de Leona Corp iniciado en el puerto: {port}")
    
    # Si detecta que estamos en la nube (Render), usa 0.0.0.0. Si estás en tu Windows local, usa 127.0.0.1
    host_ip = '0.0.0.0' if os.environ.get("RENDER") else '127.0.0.1'
    
    app.run(host=host_ip, port=port, debug=False)