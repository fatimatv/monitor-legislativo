from http.server import BaseHTTPRequestHandler
import json


LANDING_PAGE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Monitor Legislativo Digital</title>
<style>:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#07111f;color:#eaf2ff}body{max-width:760px;padding:8vh 24px;margin:auto}h1{font-size:clamp(2rem,7vw,4rem);margin-bottom:.25em}p{color:#b7c8e6;line-height:1.65}.card{margin-top:2rem;padding:1.25rem;border:1px solid #284a75;border-radius:14px;background:#0d1b30}code,a{color:#8fceff}</style>
</head><body><h1>Monitor Legislativo Digital</h1><p>Servicio de inteligencia legislativa sobre regulación digital en Perú.</p><section class="card"><strong>Servicio disponible</strong><p>El monitor se ejecuta diariamente desde un entorno con almacenamiento persistente y credenciales de Google Workspace.</p><p>Consulta técnica: <a href="/api/health"><code>/api/health</code></a>.</p></section></body></html>"""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.rstrip("/") != "/api/health":
            body = LANDING_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        payload = {
            "status": "ok",
            "service": "monitor-legislativo-digital",
            "runtime": "vercel-python",
            "monitoring": "requires persistent scheduler and state store",
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
