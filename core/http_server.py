import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer
from utils.logger import logger  
import urllib.parse

class CaptivePortalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests and serve the static HTML file."""
        try:
            # Define the path to the static file
            file_path = "web/index.html"
            
            # Open and read the file
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            
            # Send HTTP response headers
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            # Write the file content to the response
            self.wfile.write(content.encode("utf-8"))
            logger.info(f"Served GET request for {self.path}")
        except FileNotFoundError:
            # Handle the case where the file is not found
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"404 Not Found: The requested file does not exist.")
            logger.warning(f"File not found: {file_path}")
        except Exception as e:
            # Handle other unexpected errors
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"500 Internal Server Error: {str(e)}".encode("utf-8"))
            logger.error(f"Error handling GET request: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            #Parse URL-encoded form data
            form = urllib.parse.parse_qs(post_data.decode('utf-8'))
            username = form.get('username', [''])[0]
            logger.info(f"Received login attempt for username: '{username}'")
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"POST request received")
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"500 Internal Server Error: {str(e)}".encode("utf-8"))
            logger.error(f"Error handling POST request: {str(e)}")

def start_server(host="0.0.0.0", port=8080, secure=False):
    """Start the HTTP or HTTPS server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, CaptivePortalHandler)

    if secure:
        # Configure SSL context for HTTPS
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile="data/ssl/server.crt", keyfile="data/ssl/server.key")
        httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)
        logger.info(f"Starting HTTPS server on {host}:{port}")
    else:
        logger.info(f"Starting HTTP server on {host}:{port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server due to KeyboardInterrupt.")
    finally:
        httpd.server_close()
        logger.info("Server has been shut down.")