import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def registrar_log_app(usuario, accion, objetivo, estatus_http, ip_cliente, detalles):
    """Guarda eventos de seguridad en la tabla de Supabase."""
    try:
        data = {
            "usuario": usuario,
            "accion": accion,
            "objetivo": objetivo,
            "estatus_http": str(estatus_http),
            "ip_cliente": ip_cliente,
            "detalles": detalles
        }
        supabase.table("logs_aplicacion").insert(data).execute()
        # Se eliminó el print del App Log para mantener limpia la consola del servidor
    except Exception as e:
        # Silenciamos el error en consola para no generar ruido
        pass

def obtener_logs_app(limite=10):
    """Obtiene los últimos registros de auditoría directamente de Supabase."""
    try:
        # Traemos los datos, los ordenamos de más nuevo a más viejo
        respuesta = supabase.table("logs_aplicacion").select("*").order("fecha_hora", desc=True).limit(limite).execute()
        return respuesta.data
    except Exception as e:
        # Silenciamos el error en consola para no generar ruido
        return []