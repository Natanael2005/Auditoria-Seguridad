import logging

def configurar_server_logs():
    """Configura el registro de infraestructura (Server Logs) en un archivo local."""
    server_logger = logging.getLogger('server_logs')
    server_logger.setLevel(logging.INFO)
    
    if not server_logger.handlers:
        file_handler = logging.FileHandler('server_access.log')
        formatter = logging.Formatter('%(asctime)s - IP:%(clientip)s - %(method)s %(path)s - HTTP:%(status)s')
        file_handler.setFormatter(formatter)
        server_logger.addHandler(file_handler)
        
    return server_logger