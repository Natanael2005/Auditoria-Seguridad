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
        print(f"✅ [App Log] Registrado: {usuario} -> {accion}")
    except Exception as e:
        print(f"❌ Error al guardar en Supabase: {e}")