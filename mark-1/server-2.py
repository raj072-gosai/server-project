import http.server
import socketserver

# Specify the IP address of the network interface you want to bind to
HOST = '192.168.1.74'
PORT = 8000  # Port number for your server

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
    print("Server is running on http://{}:{}".format(HOST, PORT))
    print("Open your web browser and navigate to http://{}:{}".format(HOST, PORT))
    httpd.serve_forever()
