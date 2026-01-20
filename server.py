import os
import json
import importlib
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import data  # tu data.py

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.py")
JSON_FILE = os.path.join(BASE_DIR, "static", "datos.json")

last_modified_time = os.path.getmtime(DATA_FILE) if os.path.exists(DATA_FILE) else 0

# Función para generar JSON
def generar_json(force=False):
    global last_modified_time
    try:
        current_modified_time = os.path.getmtime(DATA_FILE)
        if force or current_modified_time != last_modified_time:
            try:
                importlib.reload(data)
            except Exception as e:
                print("❌ ERROR recargando data.py:", e)
                return

            os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)

            try:
                with open(JSON_FILE, "w", encoding="utf-8") as f:
                    json.dump(getattr(data, "data", {}), f, ensure_ascii=False, indent=4)
                last_modified_time = current_modified_time
                print("✅ datos.json generado automáticamente")
            except Exception as e:
                print("❌ ERROR escribiendo datos.json:", e)

    except Exception as e:
        print("❌ ERROR accediendo a data.py:", e)

# Generar JSON inicial
generar_json(force=True)

# Handler personalizado
class MiHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        generar_json(force=True)  # hot reload seguro

        parsed = urlparse(self.path)
        path = parsed.path

        # Sirve el index
        if path == "/":
            self.path = "/index.html"
            return super().do_GET()

        # Sirve JSON manualmente
        if path == "/static/datos.json":
            if os.path.exists(JSON_FILE):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                with open(JSON_FILE, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Archivo no encontrado")
            return

        # Maneja submit
        if path.startswith("/submit"):
            params = parse_qs(parsed.query)
            nombre = params.get("nombre", ["Anonimo"])[0]

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body><h1>Hola, {nombre}!</h1><p><a href='/template/index.html'>Volver</a></p></body></html>".encode())
            return

        # Todo lo demás
        super().do_GET()

# Iniciar servidor
server_address = ("0.0.0.0", PORT)
httpd = HTTPServer(server_address, MiHandler)
print(f"Servidor corriendo en http://0.0.0.0:{PORT}")

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServidor detenido manualmente.")
    httpd.server_close()
