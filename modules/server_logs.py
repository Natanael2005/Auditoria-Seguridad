import logging
import sys # Importamos sys para poder "imprimir" en la consola de Render

def configurar_server_logs():
    """Configura el registro de infraestructura (Server Logs)."""
    server_logger = logging.getLogger('server_logs')
    server_logger.setLevel(logging.INFO)
    
    if not server_logger.handlers:
        # 1. Guardar en el archivo local (Esto les sirve cuando prueban en su compu)
        file_handler = logging.FileHandler('server_access.log')
        formatter = logging.Formatter('%(asctime)s - IP:%(clientip)s - %(method)s %(path)s - HTTP:%(status)s')
        file_handler.setFormatter(formatter)
        server_logger.addHandler(file_handler)
        
        # 2. NUEVO: Enviar a la consola (Esto es para que Render lo atrape y lo muestre)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        server_logger.addHandler(stream_handler)
        
    return server_logger