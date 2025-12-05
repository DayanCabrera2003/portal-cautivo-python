import os
import sys
import threading
import time

from core.http_server import start_server
from core.session_manager import cleanup_expired_sessions
from firewall.firewall_manager import initialize_firewall
from utils.logger import logger
from utils.config import SERVER_PORT, GATEWAY_IP

def maintenance_thread():
    """Daemon thread to periodically clean up expired sessions."""
    logger.info("Starting session cleanup maintenance thread")
    while True:
        time.sleep(300)  # Sleep for 5 minutes
        cleanup_expired_sessions()

def main():
    try:
        # Cambiar al directorio base del proyecto
        base_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(base_dir)
        
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Verificar que existen los archivos necesarios
        web_dir = os.path.join(base_dir, 'web')
        if not os.path.exists(web_dir):
            logger.error(f"Web directory not found: {web_dir}")
            sys.exit(1)
        
        logger.info(f"Web files directory: {web_dir}")
        
        # Configurar firewall ANTES de iniciar el servidor
        logger.info("Initializing firewall for captive portal...")
        initialize_firewall()
        
        # Start the maintenance thread
        thread = threading.Thread(target=maintenance_thread, daemon=True)
        thread.start()
        
        logger.info(f"Starting the Captive Portal server on 0.0.0.0:{SERVER_PORT}...")
        start_server(host="0.0.0.0", port=SERVER_PORT, secure=False)
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested via KeyboardInterrupt.")
    except OSError as e:
        logger.error(f"Failed to bind the server to port {SERVER_PORT}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        logger.info("Server has been stopped.")

if __name__ == '__main__':
    main()