import threading
import time

from core.http_server import start_server
from core.session_manager import cleanup_expired_sessions
from firewall.firewall_manager import initialize_firewall, enable_ip_masquerade, enable_captive_portal_redirect
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
        # Initialize firewall rules
        logger.info("Initializing firewall for captive portal...")
        initialize_firewall()
        
        # Enable IP masquerading for NAT (change 'eth0' to your WAN interface if needed)
        enable_ip_masquerade("eth0")
        
        # Enable automatic captive portal detection via HTTP redirect
        enable_captive_portal_redirect(GATEWAY_IP, SERVER_PORT)
        
        # Start the maintenance thread
        thread = threading.Thread(target=maintenance_thread, daemon=True)
        thread.start()
        
        logger.info("Starting the Captive Portal server...")
        start_server(port=SERVER_PORT)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested via KeyboardInterrupt.")
    except OSError as e:
        logger.error(f"Failed to bind the server to port {SERVER_PORT}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        logger.info("Server has been stopped.")

if __name__ == '__main__':
    main()