import os
from flask import Flask, render_template, request
import socket
import requests as req
from supabase import create_client, Client

app = Flask(__name__)

# --- CONFIGURACIÓN DE SUPABASE ---
# Pon los datos de tu base de pruebas aquí por ahora
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# --- FUNCIÓN DE FOOTPRINTING ---
def realizar_escaneo(dominio, nombre_usuario):
    datos_log = {
        "usuario": nombre_usuario,
        "objetivo": dominio,
        "accion": "Footprinting con Flask",
        "estatus_http": "Pendiente",
        "ip_cliente": "0.0.0.0",
        "detalles": ""
    }

    try:
        ip_objetivo = socket.gethostbyname(dominio)
        response = req.get(f"http://{dominio}", timeout=5)
        
        datos_log["estatus_http"] = str(response.status_code)
        servidor = response.headers.get('Server', 'Desconocido')
        
        geo = req.get(f"http://ip-api.com/json/{ip_objetivo}").json()
        ubicacion = f"{geo.get('city')}, {geo.get('country')}"

        datos_log["ip_cliente"] = req.get('https://api.ipify.org').text
        datos_log["detalles"] = f"IP: {ip_objetivo} | Servidor: {servidor} | Ubicación: {ubicacion}"
        
        return datos_log
    except Exception as e:
        datos_log["estatus_http"] = "Error"
        datos_log["detalles"] = f"Fallo: {str(e)}"
        return datos_log

# --- RUTAS DE LA APLICACIÓN WEB ---
@app.route('/', methods=['GET', 'POST'])
def inicio():
    resultado = None
    if request.method == 'POST':
        url_ingresada = request.form.get('dominio')
        usuario_actual = "Diego_Test"
        
        # 1. Hacemos el escaneo
        resultado = realizar_escaneo(url_ingresada, usuario_actual)
        
        # 2. Guardamos en Supabase
        try:
            supabase.table("logs_aplicacion").insert(resultado).execute()
            resultado['guardado_db'] = "¡Éxito! Guardado en Supabase."
        except Exception as e:
            resultado['guardado_db'] = f"Error al guardar: {e}"
            
    return render_template('index.html', datos=resultado)

if __name__ == '__main__':
    app.run(debug=True)