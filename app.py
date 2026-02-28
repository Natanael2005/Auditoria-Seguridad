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
@app.route("/", methods=["GET", "POST"])
def login():
    if "usuario_actual" in session:
        return redirect(url_for("dashboard"))

    error_msg = None

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        ip_del_usuario = request.remote_addr

        try:
            auth_response = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            session["usuario_actual"] = auth_response.user.email

            registrar_log_app(
                usuario=email,
                accion="Login Exitoso",
                objetivo="Sistema Auth",
                estatus_http=200,
                ip_cliente=ip_del_usuario,
                detalles="Autenticación correcta.",
            )
            return redirect(url_for("dashboard"))

        except Exception as e:
            error_msg = "Credenciales incorrectas. Intenta de nuevo."
            registrar_log_app(
                usuario=email,
                accion="Intento de Login Fallido",
                objetivo="Sistema Auth",
                estatus_http=401,
                ip_cliente=ip_del_usuario,
                detalles=f"Fallo. Razón: {str(e)}",
            )

    return render_template("login.html", error=error_msg)


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    # 1. Verificamos que el usuario tenga sesión iniciada
    if "usuario_actual" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario_actual"]
    resultado_escaneo = None

    # 2. Si el usuario le dio clic al botón de "Escanear"
    if request.method == "POST":
        dominio_ingresado = request.form.get("dominio")
        ip_del_usuario = request.remote_addr

        # --- A. Usamos la herramienta de Diego ---
        resultado_escaneo = realizar_escaneo(dominio_ingresado)

        # --- B. Usamos TU sistema de Auditoría (App Logs) ---
        if resultado_escaneo["error"]:
            detalles_log = resultado_escaneo["error"]
            estatus_final = 500
        else:
            detalles_log = f"IP: {resultado_escaneo['ip']} | Servidor: {resultado_escaneo['servidor']} | País: {resultado_escaneo['ubicacion']}"
            estatus_final = resultado_escaneo["estatus"]

        # ¡Magia! Registramos el movimiento exacto en Supabase
        registrar_log_app(
            usuario=usuario,
            accion="Escaneo Footprinting",
            objetivo=dominio_ingresado,
            estatus_http=estatus_final,
            ip_cliente=ip_del_usuario,
            detalles=detalles_log,
        )

    # 3. Traemos el historial de auditoría
    logs_recientes = obtener_logs_app(10)

    # 4. Mostramos la página web y le pasamos todo
    return render_template(
        "dashboard.html",
        usuario=usuario,
        resultado=resultado_escaneo,
        logs=logs_recientes,
    )


@app.route("/logout")
def logout():
    if "usuario_actual" in session:
        usuario = session["usuario_actual"]
        session.pop("usuario_actual", None)

        registrar_log_app(
            usuario=usuario,
            accion="Logout",
            objetivo="Sistema",
            estatus_http=200,
            ip_cliente=request.remote_addr,
            detalles="El usuario cerró sesión.",
        )
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
