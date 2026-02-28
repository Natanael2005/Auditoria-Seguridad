from flask import Flask, request, render_template, redirect, url_for, session
from modules.auditoria import registrar_log_app, supabase
from modules.server_logs import configurar_server_logs
import os
from dotenv import load_dotenv

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
        'Peticion web', 
        extra={
            'clientip': request.remote_addr,
            'method': request.method,
            'path': request.path,
            'status': response.status_code
        }
    )
    return response

# =====================================================================
# RUTAS DE LA APLICACIÓN
# =====================================================================
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'usuario_actual' in session:
        return redirect(url_for('dashboard'))

    error_msg = None

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        ip_del_usuario = request.remote_addr

        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            session['usuario_actual'] = auth_response.user.email
            
            registrar_log_app(
                usuario=email, accion="Login Exitoso", objetivo="Sistema Auth", 
                estatus_http=200, ip_cliente=ip_del_usuario, detalles="Autenticación correcta."
            )
            return redirect(url_for('dashboard'))

        except Exception as e:
            error_msg = "Credenciales incorrectas. Intenta de nuevo."
            registrar_log_app(
                usuario=email, accion="Intento de Login Fallido", objetivo="Sistema Auth", 
                estatus_http=401, ip_cliente=ip_del_usuario, detalles=f"Fallo. Razón: {str(e)}"
            )

    return render_template('login.html', error=error_msg)

@app.route('/dashboard')
def dashboard():
    if 'usuario_actual' in session:
        # ¡Aquí ya estamos llamando al nuevo archivo dashboard.html!
        return render_template('dashboard.html', usuario=session['usuario_actual'])
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    if 'usuario_actual' in session:
        usuario = session['usuario_actual']
        session.pop('usuario_actual', None)
        
        registrar_log_app(
            usuario=usuario, accion="Logout", objetivo="Sistema", 
            estatus_http=200, ip_cliente=request.remote_addr, detalles="El usuario cerró sesión."
        )
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)