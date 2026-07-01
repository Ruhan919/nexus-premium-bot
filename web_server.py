from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "service": "NEXUS Premium Bot v5.0",
            "status": "running",
            "bot_token": os.environ.get("BOT_TOKEN", "")[:10] + "...",
            "owner_id": os.environ.get("OWNER_ID", "N/A")
        }).encode())
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f'Health server running on port {port}')
    server.serve_forever()
