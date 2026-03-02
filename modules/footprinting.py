import socket
import requests as req

def realizar_escaneo(dominio):

    resultado = {
        "dominio": dominio,
        "ip": "Desconocida",
        "servidor": "Desconocido",
        "ubicacion": "Desconocida",
        "estatus": 500,
        "error": None
    }
    
    try:
        # 1. Obtener IP
        ip_objetivo = socket.gethostbyname(dominio)
        resultado["ip"] = ip_objetivo
        
        # 2. Obtener Estatus y Servidor (Headers)
        response = req.get(f"http://{dominio}", timeout=5)
        resultado["estatus"] = response.status_code
        resultado["servidor"] = response.headers.get('Server', 'Desconocido')
        
        # 3. Geolocalización
        geo = req.get(f"http://ip-api.com/json/{ip_objetivo}").json()
        if geo.get('status') == 'success':
            resultado["ubicacion"] = f"{geo.get('city')}, {geo.get('country')}"

        return resultado
        
    except Exception as e:
        resultado["error"] = f"Fallo en la conexión: {str(e)}"
        return resultado