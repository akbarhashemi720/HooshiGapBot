import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# HTTP server فوری بالا بیاد
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

PORT = int(os.environ.get("PORT", 10000))
server = HTTPServer(("0.0.0.0", PORT), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
print(f"✅ HTTP server on port {PORT}")

# event loop بساز و bot رو اجرا کن
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import bot
bot.main()
