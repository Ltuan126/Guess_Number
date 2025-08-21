# client/run_client.py
import http.server
import socketserver

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    print(f"Serving client at http://localhost:{PORT}/")
    httpd.serve_forever()
