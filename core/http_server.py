import ssl
import urllib.parse
import http.cookies
import re

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from utils.logger import logger
from core.auth_manager import validate_credentials
from core.session_manager import create_session, get_session, destroy_session
from firewall.firewall_manager import allow_user_access, revoke_access
  


class CaptivePortalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests and serve the static HTML file."""
        if self.path == "/logout":
            # Handle logout: retrieve session ID, destroy session, revoke access, expire cookie
            session_id = None
            user_ip = None
            if 'Cookie' in self.headers:
                cookie = http.cookies.SimpleCookie(self.headers['Cookie'])
                if 'session_id' in cookie:
                    session_id = cookie['session_id'].value
                    session = get_session(session_id)
                    if session:
                        user_ip = session["user_info"].get("ip")
                        destroy_session(session_id)
                        logger.info(f"Session {session_id} destroyed for logout")
            
            if user_ip:
                revoke_access(user_ip)
                logger.info(f"Firewall access revoked for IP {user_ip} on logout")
            
            # Send response with expired cookie
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Set-Cookie", "session_id=; HttpOnly; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT")
            self.end_headers()
            self.wfile.write(b"<html><body>Logged out successfully.</body></html>")
            return
        
        # Check for session cookie and validate
        if 'Cookie' in self.headers:
            cookie = http.cookies.SimpleCookie(self.headers['Cookie'])
            if 'session_id' in cookie:
                session_id = cookie['session_id'].value
                session = get_session(session_id)
                current_ip = self.client_address[0]
                stored_ip = session["user_info"].get("ip") if session else None
                if session and current_ip == stored_ip:
                    # Valid session, redirect to access granted endpoint (using existing /login_succes as the success page)
                    self.send_response(302)
                    self.send_header("Location", "/login_succes")
                    self.end_headers()
                    logger.info(f"Valid session for user '{session.get('username', 'unknown')}'. Redirected to /login_succes.")
                    return
                elif session:
                    logger.warning(f"IP mismatch for session {session_id}: current IP {current_ip}, stored IP {stored_ip}. Treating as invalid session.")
        
        # If no valid session, serve the appropriate page
        try:
            # Define the path to the static file
            if self.path == "/login_succes":
                file_path = "web/login_succes.html"
            else:
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
            # Parse URL-encoded form data
            form = urllib.parse.parse_qs(post_data.decode('utf-8'))
            username = form.get('username', [''])[0]
            password = form.get('password', [''])[0]
            
            # Input validation
            if not re.match(r'^[a-zA-Z0-9_-]{3,20}$', username):
                self.send_response(400)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Invalid username: must be 3-20 characters, alphanumeric with underscores or hyphens.")
                logger.warning(f"Invalid username input: '{username}'")
                return
            if not re.match(r'^[a-zA-Z0-9_-]{6,50}$', password):
                self.send_response(400)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Invalid password: must be 6-50 characters, alphanumeric with underscores or hyphens.")
                logger.warning(f"Invalid password input for username: '{username}'")
                return
            
            logger.info(f"Received login attempt for username: '{username}'")
            if validate_credentials(username, password):
                # Create session and set cookie
                client_ip = self.client_address[0]
                session_id = create_session({"username": username, "ip": client_ip})
                self.send_response(302)
                self.send_header("Location", "/login_succes")
                self.send_header("Set-Cookie", f"session_id={session_id}; HttpOnly; Path=/")
                self.end_headers()
                logger.info(f"User '{username}' authenticated. Session started and redirected to /login_succes.")
                
                #Retrieve client's source IP and allow acces
                allow_user_access(client_ip)
                logger.info(f"Firewall acces grantes for IP {client_ip} after authentication")
            else:
                file_path = "web/login_failed.html"
                with open(file_path, "r", encoding="utf-8") as file:
                    response_html = file.read().format(username=username)
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(response_html.encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"500 Internal Server Error: {str(e)}".encode("utf-8"))
            logger.error(f"Error handling POST request: {str(e)}")

def start_server(host="0.0.0.0", port=8080, secure=True):
    """Start the HTTP or HTTPS server with concurrent request handling."""
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, CaptivePortalHandler)

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