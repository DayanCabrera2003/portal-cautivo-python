import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer

class CaptivePortalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Welcome!</h1></body></html>")
    
    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        print(f"Received POST data: {post_data.decode('utf-8')}")
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"POST request received")
    
def start_server(host="0.0.0.0", port=8080, secure=False):
    """Start the HTTP or HTTPS server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, CaptivePortalHandler)

    if secure:
        # Configure SSL context for HTTPS
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(certfile="data/ssl/server.crt", keyfile="data/ssl/server.key")
        httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)
        print(f"Starting HTTPS server on {host}:{port}")
    else:
        print(f"Starting HTTP server on {host}:{port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()
        