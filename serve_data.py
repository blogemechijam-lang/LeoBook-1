
import http.server
import socketserver
import os

PORT = 8000
DIRECTORY = "Data/Store"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

if __name__ == "__main__":
    if not os.path.exists(DIRECTORY):
        print(f"Error: Directory {DIRECTORY} not found.")
        exit(1)
        
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving {DIRECTORY} at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
