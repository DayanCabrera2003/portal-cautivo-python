from core.http_server import start_server
from utils.logger import logger
from utils.config import SERVER_PORT

def main():
    try:
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