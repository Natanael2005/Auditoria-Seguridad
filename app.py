from flask import Flask, request, render_template, redirect, url_for, session
from modules.auditoria import registrar_log_app, supabase
from modules.server_logs import configurar_server_logs
import os
from modules.footprinting import realizar_escaneo
from dotenv import load_dotenv
from modules.auditoria import registrar_log_app, obtener_logs_app, supabase

load_dotenv()

app = Flask(__name__)
app.secret_key = "clave_super_secreta_auditoria_2026"


# =====================================================================
# CONFIGURACIÓN DE LOGS DE SERVIDOR
# =====================================================================
server_logger = configurar_server_logs()


@app.after_request
def log_server_request(response):
    """Guarda automáticamente cada petición HTTP en el archivo de texto local."""
    server_logger.info(
        "Peticion web",
        extra={
            "clientip": request.remote_addr,
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
        ip_del_usuario = request.remote_addr

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
        ip_del_usuario = request.remote_addr

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
    ip_del_usuario = request.remote_addr

    if tipo_accion == "nomina":
        detalles, estatus, msj = "Visualizó recibo de nómina.", 200, "📄 Descargando recibo de nómina..."
    elif tipo_accion == "directorio":
        detalles, estatus, msj = "Accedió al directorio de empleados.", 200, "👥 Abriendo directorio..."
    elif tipo_accion == "mensajes":
        detalles, estatus, msj = "Revisó bandeja de entrada.", 200, "✉️ No tienes mensajes nuevos."
    elif tipo_accion == "finanzas":
        detalles, estatus, msj = "ALERTA: Intento de acceso a DB Financiera.", 403, "❌ Error 403: Permisos insuficientes."
    else:
        detalles, estatus, msj = "Acción desconocida.", 400, "Acción no válida."

    registrar_log_app(usuario=usuario, accion=f"Módulo: {tipo_accion}", objetivo="Datos Internos", estatus_http=estatus, ip_cliente=ip_del_usuario, detalles=detalles)
    return render_template("dashboard.html", usuario=usuario, mensaje=msj)

@app.route("/admin_financiero")
def ruta_finanzas():
    """Ruta oculta de alta sensibilidad"""
    usuario = session.get("usuario_actual", "Anonimo")
    registrar_log_app(
        usuario=usuario, 
        accion="Acceso a Ruta Oculta", 
        objetivo="Finanzas_Direct", 
        estatus_http=403, 
        ip_cliente=request.remote_addr, 
        detalles="ALERTA: Intento de acceso directo a base de datos financiera."
    )
    # Mostramos un error 403 real para la auditoría
    return "<h1>403 Forbidden</h1><p>No tienes permisos para estar aquí. Tu IP ha sido registrada.</p>", 403

@app.route("/cctv_interno")
def ruta_cctv():
    """Ruta oculta de cámaras"""
    usuario = session.get("usuario_actual", "Anonimo")
    registrar_log_app(
        usuario=usuario, 
        accion="Acceso a Ruta Oculta", 
        objetivo="CCTV_Stream", 
        estatus_http=403, 
        ip_cliente=request.remote_addr, 
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
        registrar_log_app(usuario=session["usuario_actual"], accion="Logout", objetivo="Portal Leona Corp", estatus_http=200, ip_cliente=request.remote_addr, detalles="Sesión cerrada.")
        session.pop("usuario_actual", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    # Render asigna un puerto dinámico, si no existe usamos el 5000 por defecto
    port = int(os.environ.get("PORT", 5000))
    # Importante: host='0.0.0.0' para que sea accesible desde internet
    app.run(host='0.0.0.0', port=port, debug=False)