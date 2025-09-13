import json
import logging
import time
import threading
import socket
import http.server
import socketserver
import webbrowser
import urllib.parse
from pathlib import Path
from typing import Dict, Any
from config import TICKETS

# Configure logging
crud_logger = logging.getLogger('napkinwire_crud')

def get_project_root() -> Path:
    """Get project root from TICKETS file path directory"""
    tickets_path = Path(TICKETS)
    return tickets_path.parent

def napkinwire_spawn_diagram_editor() -> Dict[str, Any]:
    """Spawn local HTTP server for diagram editor and return ASCII diagram data

    Starts HTTP server on localhost, opens browser to diagram.html, waits for POST request
    with ASCII data, returns the diagram representation.

    Returns:
        Dict with diagram data or error message
    """
    crud_logger.info("Starting HTTP server for diagram editor")

    try:
        # Get project root and web directory path
        project_root = get_project_root()
        web_dir = project_root / "web"

        if not web_dir.exists():
            return {
                "error": f"Web directory not found: {web_dir}",
                "success": False
            }

        diagram_html_path = web_dir / "diagram.html"
        if not diagram_html_path.exists():
            return {
                "error": f"Diagram HTML file not found: {diagram_html_path}",
                "success": False
            }

        # Find available port starting from 8765
        def find_free_port(start_port=8765):
            for port in range(start_port, start_port + 100):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('localhost', port))
                        return port
                except OSError:
                    continue
            raise Exception("No free port found in range 8765-8864")

        port = find_free_port()
        crud_logger.info(f"Using port {port} for HTTP server")

        # Storage for received diagram data
        received_data = {"diagram": None, "error": None, "received": False}

        class DiagramHTTPHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(web_dir), **kwargs)

            def do_POST(self):
                if self.path == '/send_to_claude':
                    try:
                        content_length = int(self.headers.get('Content-Length', 0))
                        post_data = self.rfile.read(content_length)

                        # Parse form data or JSON
                        if self.headers.get('Content-Type', '').startswith('application/json'):
                            data = json.loads(post_data.decode('utf-8'))
                            ascii_data = data.get('diagram_data', '')
                        else:
                            # Form data
                            parsed_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
                            ascii_data = parsed_data.get('diagram_data', [''])[0]

                        if ascii_data:
                            received_data["diagram"] = ascii_data
                            received_data["received"] = True
                            crud_logger.info(f"Received diagram data: {len(ascii_data)} characters")

                            # Send success response
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                        else:
                            self.send_response(400)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(json.dumps({"error": "No diagram data"}).encode('utf-8'))

                    except Exception as e:
                        crud_logger.error(f"Error handling POST request: {e}")
                        received_data["error"] = str(e)
                        received_data["received"] = True

                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_OPTIONS(self):
                # Handle CORS preflight
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()

            def log_message(self, format, *args):
                # Suppress default server logs to keep output clean
                pass

        # Start HTTP server in background thread
        with socketserver.TCPServer(("localhost", port), DiagramHTTPHandler) as httpd:
            httpd.timeout = 1  # Short timeout for serve_request to allow checking received_data

            server_thread = threading.Thread(target=lambda: httpd.serve_forever())
            server_thread.daemon = True
            server_thread.start()

            crud_logger.info(f"HTTP server started on http://localhost:{port}")

            # Open browser to diagram.html
            diagram_url = f"http://localhost:{port}/diagram.html"
            try:
                webbrowser.open(diagram_url)
                crud_logger.info(f"Opened browser to {diagram_url}")
            except Exception as e:
                crud_logger.warning(f"Failed to open browser automatically: {e}")
                return {
                    "error": f"Server started but failed to open browser. Please go to {diagram_url}",
                    "success": False
                }

            # Wait for data or timeout
            timeout_seconds = 60
            start_time = time.time()

            while not received_data["received"] and (time.time() - start_time) < timeout_seconds:
                time.sleep(0.5)

            # Shutdown server
            httpd.shutdown()
            server_thread.join(timeout=2)

            # Return result
            if received_data["received"]:
                if received_data["diagram"]:
                    crud_logger.info("Successfully received diagram data from HTTP server")
                    return {
                        "success": True,
                        "diagram_data": received_data["diagram"],
                        "method": "http_server"
                    }
                else:
                    crud_logger.error(f"HTTP server error: {received_data['error']}")
                    return {
                        "success": False,
                        "error": received_data["error"] or "Unknown error receiving diagram data"
                    }
            else:
                crud_logger.error("HTTP server timed out waiting for diagram data")
                return {
                    "success": False,
                    "error": "Diagram editor timed out after 60 seconds"
                }

    except Exception as e:
        crud_logger.error(f"Error in HTTP server diagram editor: {e}")
        return {
            "error": str(e),
            "success": False,
            "message": "Failed to start HTTP server for diagram editor"
        }

def napkinwire_spawn_ui_mockup_editor() -> Dict[str, Any]:
    """Spawn local HTTP server for UI mockup editor and return ASCII mockup data

    Starts HTTP server on localhost, opens browser to ui.html, waits for POST request
    with ASCII data, returns the UI mockup representation.

    Returns:
        Dict with UI mockup data or error message
    """
    crud_logger.info("Starting HTTP server for UI mockup editor")

    try:
        # Get project root and web directory path
        project_root = get_project_root()
        web_dir = project_root / "web"

        if not web_dir.exists():
            return {
                "error": f"Web directory not found: {web_dir}",
                "success": False
            }

        ui_html_path = web_dir / "ui.html"
        if not ui_html_path.exists():
            return {
                "error": f"UI HTML file not found: {ui_html_path}",
                "success": False
            }

        # Find available port starting from 8766
        def find_free_port(start_port=8766):
            for port in range(start_port, start_port + 100):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('localhost', port))
                        return port
                except OSError:
                    continue
            raise Exception("No free port found in range 8766-8865")

        port = find_free_port()
        crud_logger.info(f"Using port {port} for UI mockup HTTP server")

        # Storage for received UI mockup data
        received_data = {"ui_mockup": None, "error": None, "received": False}

        class UIMockupHTTPHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(web_dir), **kwargs)

            def do_POST(self):
                if self.path == '/send_to_claude':
                    try:
                        content_length = int(self.headers.get('Content-Length', 0))
                        post_data = self.rfile.read(content_length)

                        # Parse form data or JSON
                        if self.headers.get('Content-Type', '').startswith('application/json'):
                            data = json.loads(post_data.decode('utf-8'))
                            ascii_data = data.get('ui_mockup_data', '')
                        else:
                            # Form data
                            parsed_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
                            ascii_data = parsed_data.get('ui_mockup_data', [''])[0]

                        if ascii_data:
                            received_data["ui_mockup"] = ascii_data
                            received_data["received"] = True
                            crud_logger.info(f"Received UI mockup data: {len(ascii_data)} characters")

                            # Send success response
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                        else:
                            self.send_response(400)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(json.dumps({"error": "No UI mockup data"}).encode('utf-8'))

                    except Exception as e:
                        crud_logger.error(f"Error handling POST request: {e}")
                        received_data["error"] = str(e)
                        received_data["received"] = True

                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_OPTIONS(self):
                # Handle CORS preflight
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()

            def log_message(self, format, *args):
                # Suppress default server logs to keep output clean
                pass

        # Start HTTP server in background thread
        with socketserver.TCPServer(("localhost", port), UIMockupHTTPHandler) as httpd:
            httpd.timeout = 1  # Short timeout for serve_request to allow checking received_data

            server_thread = threading.Thread(target=lambda: httpd.serve_forever())
            server_thread.daemon = True
            server_thread.start()

            crud_logger.info(f"HTTP server started on http://localhost:{port}")

            # Open browser to ui.html
            ui_url = f"http://localhost:{port}/ui.html"
            try:
                webbrowser.open(ui_url)
                crud_logger.info(f"Opened browser to {ui_url}")
            except Exception as e:
                crud_logger.warning(f"Failed to open browser automatically: {e}")
                return {
                    "error": f"Server started but failed to open browser. Please go to {ui_url}",
                    "success": False
                }

            # Wait for data or timeout
            timeout_seconds = 60
            start_time = time.time()

            while not received_data["received"] and (time.time() - start_time) < timeout_seconds:
                time.sleep(0.5)

            # Shutdown server
            httpd.shutdown()
            server_thread.join(timeout=2)

            # Return result
            if received_data["received"]:
                if received_data["ui_mockup"]:
                    crud_logger.info("Successfully received UI mockup data from HTTP server")
                    return {
                        "success": True,
                        "ui_mockup_data": received_data["ui_mockup"],
                        "method": "http_server"
                    }
                else:
                    crud_logger.error(f"HTTP server error: {received_data['error']}")
                    return {
                        "success": False,
                        "error": received_data["error"] or "Unknown error receiving UI mockup data"
                    }
            else:
                crud_logger.error("HTTP server timed out waiting for UI mockup data")
                return {
                    "success": False,
                    "error": "UI mockup editor timed out after 60 seconds"
                }

    except Exception as e:
        crud_logger.error(f"Error in HTTP server UI mockup editor: {e}")
        return {
            "error": str(e),
            "success": False,
            "message": "Failed to start HTTP server for UI mockup editor"
        }