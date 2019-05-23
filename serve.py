
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import datahandlers as dh

# Assemble a sample output for the file
output = dh.assembleOutput()

HOST = 'localhost'
PORT_NUMBER = 8003

class Server(BaseHTTPRequestHandler):
    def do_HEAD(self):
        return

    def do_GET(self):
        self.respond()

    def do_POST(self):
        return

    def handle_http(self, status, content_type):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.end_headers()
        # return bytes("Hello World", "UTF-8")
        return bytes(output, "UTF-8")

    def respond(self):
        content = self.handle_http(200, 'text/html')
        self.wfile.write(content)

httpd = HTTPServer((HOST, PORT_NUMBER), Server)
try:
        print("Starting HTTP server on "+str(HOST)+":"+str(PORT_NUMBER)+".")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("HTTP server failed.")
    pass
httpd.server_close()
