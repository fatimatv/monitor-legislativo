from __future__ import annotations

from datetime import date
from http.server import BaseHTTPRequestHandler
import json
from pathlib import Path
from urllib.request import Request, urlopen


API_BASE = "https://api.congreso.gob.pe/spley-portal-service"
IALAW_LOGO = Path(__file__).resolve().parent.parent / "assets" / "ialaw-horizontal-blue-bg.png"
TOPICS = {
    "IA": ("inteligencia artificial", "ia generativa", "algoritmo", "algorítmico", "automatizado"),
    "Datos": ("datos personales", "protección de datos", "privacidad", "biometr", "reconocimiento facial", "videovigilancia", "tacógrafo digital", "tacografo digital"),
    "Plataformas": ("redes sociales", "plataforma digital", "comercio electrónico", "marketplace", "juegos a distancia", "apuestas deportivas a distancia"),
    "Ciberseguridad": ("ciberseguridad", "ciberdelincuencia", "delito informático", "fraude informático"),
    "Telecom": ("telecomunic", "internet", "acceso a internet", "conectividad", "banda ancha", "espectro radioeléctrico"),
    "Gobierno digital": ("gobierno digital", "interoperabilidad", "firma digital", "firma electrónica", "firmar electrónicamente", "identidad digital"),
    "Fintech": ("fintech", "paytech", "billetera digital", "billeteras digitales", "billetera electrónica", "dinero electrónico", "pago digital", "pagos digitales", "banca digital", "criptoactivo"),
    "Derechos digitales": ("derechos digitales", "derecho digital", "ciudadanía digital", "libertad en internet", "accesibilidad digital"),
    "Aplicaciones": ("aplicación digital", "aplicaciones digitales", "aplicación móvil", "aplicaciones móviles", "app móvil", "servicio digital", "software como servicio"),
    "Transformación digital": ("transformación digital", "innovación digital", "innovación tecnológica", "tecnologías emergentes", "ecosistema digital"),
    "Servicios regulados": ("servicios regulados", "compensaciones automáticas", "interrupciones de servicios"),
}


def official_json(url: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Accept": "application/json", "User-Agent": "monitor-legislativo-vercel/0.1"}
    if body:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method="POST" if body else "GET")
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def classify(title: str) -> list[str]:
    text = title.casefold()
    return [label for label, terms in TOPICS.items() if any(term in text for term in terms)]


def latest_projects() -> dict:
    periods = official_json(f"{API_BASE}/periodo-parlamentario").get("data", [])
    today = date.today()
    active = next((item for item in periods if date.fromisoformat(item["fecIni"][:10]) <= today <= date.fromisoformat(item["fecFin"][:10])), periods[0])
    filters = {"perParId": active["perParId"], "codTipoParl": "D", "perLegId": None, "comisionId": None, "estadoId": None, "congresistaId": None, "grupoParlamentarioId": None, "proponenteId": None, "legislaturaId": None, "fecPresentacionDesde": None, "fecPresentacionHasta": None, "pleyNum": None, "palabras": None, "tipoFirmanteId": None, "conAcumulado": False, "pageSize": 50, "rowStart": 0}
    result = official_json(f"{API_BASE}/proyecto-ley/lista-con-filtro", filters).get("data", {})
    projects = []
    for item in result.get("proyectos", []):
        title = item.get("titulo", "").strip()
        projects.append({"id": item.get("proyectoLey"), "date": item.get("fecPresentacion", "")[:10], "title": title, "status": item.get("desEstado", ""), "tags": classify(title), "url": f"https://wb2server.congreso.gob.pe/spley-portal/#/diputados/expediente/{item.get('perParId')}/{item.get('pleyNum')}"})
    return {"period": active["desPerParAbrev"], "total": result.get("rowsTotal", 0), "projects": projects}


LANDING_PAGE = r"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>IALAW · Radar Legislativo Digital</title><style>
:root{--blue:#011EF4;--deep:#0118BF;--yellow:#FBBB02;--ink:#17214c;--muted:#636466;--panel:#f7f8ff;--line:#d4d5d5;--mono:ui-monospace,Consolas,monospace;--sans:Poppins,Arial,sans-serif}*{box-sizing:border-box}body{margin:0;color:var(--ink);font-family:var(--sans);background:linear-gradient(90deg,transparent 49.9%,rgba(1,30,244,.035) 50%,transparent 50.1%)}.skip{position:absolute;left:-9999px}.skip:focus{left:1rem;top:1rem;background:#fff;color:var(--blue);padding:.75rem;z-index:9}.shell{max-width:1180px;margin:auto;padding:28px 24px 70px}.mast{display:flex;justify-content:space-between;gap:2rem;padding:28px;position:relative;overflow:hidden;background:var(--blue);border-bottom:7px solid var(--yellow)}.mast:after{content:"";position:absolute;right:-5rem;bottom:-8rem;width:26rem;height:26rem;border:1px solid rgba(255,255,255,.26);border-radius:50%;box-shadow:0 0 0 28px rgba(255,255,255,.06)}.mast>*{position:relative;z-index:1}.brand-logo{display:block;width:158px;height:auto;margin:0 0 28px}.eyebrow,.mono{font:12px var(--mono);letter-spacing:.11em;text-transform:uppercase;color:var(--yellow)}h1{font-size:clamp(2.5rem,7vw,6rem);letter-spacing:-.07em;line-height:.9;margin:.22rem 0 1rem;color:#fff}.lede{max-width:650px;color:#fff;line-height:1.6}.status{align-self:start;border:1px solid var(--yellow);padding:.6rem .8rem;font:12px var(--mono);color:#fff;background:rgba(0,0,0,.12);white-space:nowrap}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin:28px 0}.metric{background:var(--panel);padding:20px}.metric strong{display:block;font:clamp(2rem,5vw,3.4rem) var(--mono);color:var(--blue)}.metric span,.hint{color:var(--muted);font-size:.85rem}.toolbar{display:grid;grid-template-columns:1fr 210px auto auto;gap:10px;margin:18px 0 8px}input,select,button{min-height:48px;border:1px solid var(--line);background:#fff;color:var(--ink);padding:0 14px;font:14px var(--sans)}button{background:var(--blue);color:#fff;border-color:var(--blue);font-weight:800;cursor:pointer}button:hover{background:var(--deep)}button.secondary{background:#fff;color:var(--blue)}button.secondary:hover{background:#eef0ff}button:focus-visible,input:focus-visible,select:focus-visible,a:focus-visible{outline:3px solid var(--yellow);outline-offset:3px}.rail{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-top:24px}.project{border:1px solid var(--line);border-top:4px solid var(--blue);background:#fff;padding:18px;min-height:220px;display:flex;flex-direction:column;transition:transform .2s ease,border-color .2s ease}.project:hover{transform:translateY(-4px);border-top-color:var(--yellow)}.project h2{font-size:1.05rem;line-height:1.35;margin:15px 0;color:var(--ink)}.meta{display:flex;justify-content:space-between;gap:.5rem;color:var(--muted);font:12px var(--mono)}.tag{display:inline-block;border:1px solid var(--blue);color:var(--blue);padding:4px 6px;margin:0 4px 4px 0;font:11px var(--mono)}.tag.neutral{border-color:var(--line);color:var(--muted)}.project a{margin-top:auto;color:var(--blue);font-weight:700;text-decoration:none}.empty{border:1px dashed var(--line);padding:34px;color:var(--muted);grid-column:1/-1}.footer{margin-top:38px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:.8rem}.footer strong{color:var(--blue)}@media(max-width:820px){.mast{display:block}.status{display:inline-block;margin-top:1rem}.metrics,.toolbar{grid-template-columns:1fr}.shell{padding:16px 14px 50px}.brand-logo{width:135px}}@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head><body><a class="skip" href="#results">Ir a resultados</a><main class="shell"><header class="mast"><div><img class="brand-logo" src="/brand/ialaw-horizontal-blue-bg.png" alt="IALAW Digital Lawyers"><div class="eyebrow">Congreso del Perú · Fuente oficial</div><h1>Radar<br>legislativo.</h1><p class="lede">Iniciativas con posible impacto para el ecosistema digital. La clasificación es un filtro inicial configurable, no una conclusión jurídica.</p></div><div class="status" id="system-status">● CONECTANDO</div></header><section class="metrics" aria-label="Métricas"><div class="metric"><strong id="metric-total">—</strong><span>iniciativas del período</span></div><div class="metric"><strong id="metric-loaded">—</strong><span>revisadas en esta consulta</span></div><div class="metric"><strong id="metric-relevant">—</strong><span>con señal digital</span></div></section><section aria-label="Filtros"><div class="toolbar"><input id="search" type="search" placeholder="Buscar título o estado"><select id="topic"><option value="">Todas las categorías</option></select><button id="scope" class="secondary" type="button" aria-pressed="false">Ver todas</button><button id="reload" type="button">Actualizar datos</button></div><p id="scope-hint" class="hint">Mostrando solo iniciativas con señal digital.</p></section><section id="results" class="rail" aria-live="polite"><div class="empty">Cargando iniciativas oficiales…</div></section><footer class="footer"><strong>IALAW · Digital Lawyers</strong> — Inteligencia legislativa para decisiones digitales informadas.</footer></main><script>
let data=[],showAll=false;const el=id=>document.getElementById(id);const esc=v=>String(v||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));function card(p){const tags=p.tags.map(t=>'<span class="tag">'+esc(t)+'</span>').join('')||'<span class="tag neutral">Sin clasificación digital</span>';return '<article class="project"><div class="meta"><span>'+esc(p.date||'Sin fecha')+'</span><span>'+esc(p.status||'—')+'</span></div><h2>'+esc(p.title)+'</h2><div>'+tags+'</div><p class="mono">'+esc(p.id)+'</p><a href="'+esc(p.url)+'" target="_blank" rel="noopener">Ver expediente oficial ↗</a></article>'}function scopeCopy(){el('scope').textContent=showAll?'Ver solo señal digital':'Ver todas';el('scope').setAttribute('aria-pressed',String(showAll));el('scope-hint').textContent=showAll?'Mostrando todas las iniciativas recientes, incluidas las que están fuera del alcance digital.':'Mostrando solo iniciativas con señal digital.'}function render(){const q=el('search').value.toLowerCase(),topic=el('topic').value;const shown=data.filter(p=>(showAll||p.tags.length)&&JSON.stringify(p).toLowerCase().includes(q)&&(!topic||p.tags.includes(topic)));el('metric-loaded').textContent=data.length;el('metric-relevant').textContent=data.filter(p=>p.tags.length).length;el('results').innerHTML=shown.length?shown.map(card).join(''):'<div class="empty">No hay iniciativas con señal digital que coincidan con este filtro.</div>'}async function load(){el('system-status').textContent='● ACTUALIZANDO';el('results').innerHTML='<div class="empty">Consultando la fuente oficial…</div>';try{const r=await fetch('/api/projects');if(!r.ok)throw Error();const payload=await r.json();data=payload.projects;el('metric-total').textContent=payload.total;const topics=[...new Set(data.flatMap(p=>p.tags))];el('topic').innerHTML='<option value="">Todas las categorías</option>'+topics.map(t=>'<option>'+esc(t)+'</option>').join('');scopeCopy();render();el('system-status').textContent='● FUENTE ACTUALIZADA'}catch{el('system-status').textContent='● FUENTE NO DISPONIBLE';el('results').innerHTML='<div class="empty">No fue posible consultar el Congreso en este momento. Intenta actualizar.</div>'}}el('search').addEventListener('input',render);el('topic').addEventListener('change',render);el('scope').addEventListener('click',()=>{showAll=!showAll;scopeCopy();render()});el('reload').addEventListener('click',load);load();
</script></body></html>"""


class handler(BaseHTTPRequestHandler):
    def _json(self, payload: dict, status: int = 200, cache: str = "no-store") -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(body)

    def _asset(self, path: Path, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        self.end_headers()
        self.wfile.write(path.read_bytes())

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path == "/brand/ialaw-horizontal-blue-bg.png":
            self._asset(IALAW_LOGO, "image/png")
            return
        if path == "/api/health":
            self._json({"status": "ok", "service": "monitor-legislativo-digital", "runtime": "vercel-python", "monitoring": "dashboard uses live official metadata"})
            return
        if path == "/api/projects":
            try:
                self._json(latest_projects(), cache="s-maxage=300, stale-while-revalidate=600")
            except Exception:
                self._json({"error": "No se pudo consultar la fuente oficial."}, status=502)
            return
        body = LANDING_PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
