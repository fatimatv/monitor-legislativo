from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterator
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .normalization import API_URL, normalize_project
from .models import Proposition


class CongressSourceError(RuntimeError):
    pass


@dataclass(slots=True)
class CongressClient:
    timeout_seconds: int = 30
    max_retries: int = 3
    page_size: int = 50

    def _request(self, url: str, method: str = "GET", body: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
        payload = json.dumps(body).encode("utf-8") if body is not None else None
        request_headers = {"Accept": "application/json", "User-Agent": "monitor-legislativo-digital/0.1"}
        if payload:
            request_headers["Content-Type"] = "application/json"
        request_headers.update(headers or {})
        for attempt in range(self.max_retries):
            try:
                request = Request(url, data=payload, method=method, headers=request_headers)
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    response_body = response.read()
                    content_type = response.headers.get_content_type()
                    if content_type == "application/json":
                        return json.loads(response_body.decode("utf-8"))
                    return response_body, dict(response.headers.items())
            except (HTTPError, URLError, TimeoutError) as exc:
                if attempt + 1 == self.max_retries:
                    raise CongressSourceError(f"Error al consultar {url}: {exc}") from exc
                time.sleep(2**attempt)
        raise AssertionError("unreachable")

    def periods(self) -> list[dict[str, Any]]:
        response = self._request(f"{API_URL}/periodo-parlamentario")
        data = response.get("data") if isinstance(response, dict) else None
        if not isinstance(data, list) or not data:
            raise CongressSourceError("Respuesta inesperada: no hay períodos parlamentarios.")
        return data

    def current_period(self) -> int:
        today = date.today()
        for period in self.periods():
            start = date.fromisoformat(str(period["fecIni"])[:10])
            end = date.fromisoformat(str(period["fecFin"])[:10])
            if start <= today <= end:
                return int(period["perParId"])
        return int(self.periods()[0]["perParId"])

    def search_page(self, period: int, row_start: int = 0) -> tuple[list[Proposition], int]:
        payload = {
            "perParId": period, "codTipoParl": "D", "perLegId": None, "comisionId": None,
            "estadoId": None, "congresistaId": None, "grupoParlamentarioId": None,
            "proponenteId": None, "legislaturaId": None, "fecPresentacionDesde": None,
            "fecPresentacionHasta": None, "pleyNum": None, "palabras": None,
            "tipoFirmanteId": None, "conAcumulado": False, "pageSize": self.page_size,
            "rowStart": row_start,
        }
        response = self._request(f"{API_URL}/proyecto-ley/lista-con-filtro", "POST", payload)
        data = response.get("data") if isinstance(response, dict) else None
        projects = data.get("proyectos") if isinstance(data, dict) else None
        total = data.get("rowsTotal") if isinstance(data, dict) else None
        if not isinstance(projects, list) or not isinstance(total, int):
            raise CongressSourceError("Respuesta inesperada de lista-con-filtro; se detiene para evitar un falso cero.")
        return [normalize_project(item) for item in projects], total

    def iter_projects(self, period: int, start_date: date | None = None) -> Iterator[Proposition]:
        row_start = 0
        while True:
            projects, total = self.search_page(period, row_start)
            if not projects:
                return
            for project in projects:
                if start_date is None or project.presented_on is None or project.presented_on >= start_date:
                    yield project
            if row_start + len(projects) >= total:
                return
            if start_date and projects[-1].presented_on and projects[-1].presented_on < start_date:
                return
            row_start += len(projects)

    @staticmethod
    def encrypt_path_segment(value: int | str) -> str:
        """Coincide con AES-ECB/PKCS7 del frontend; depende de pycryptodome."""
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import pad
        except ImportError as exc:
            raise CongressSourceError("Falta pycryptodome; instale las dependencias del proyecto.") from exc
        cipher = AES.new(b"ProdALg5ZrAsxBMD", AES.MODE_ECB)
        encrypted = cipher.encrypt(pad(str(value).encode("utf-8"), AES.block_size))
        return base64.urlsafe_b64encode(encrypted).decode("ascii").rstrip("=")

    def detail(self, period: int, number: int, chamber: str = "D") -> dict[str, Any]:
        period_token = self.encrypt_path_segment(period)
        number_token = self.encrypt_path_segment(number)
        response = self._request(f"{API_URL}/expediente/{period_token}/{number_token}?codTipoParl={chamber}")
        data = response.get("data") if isinstance(response, dict) else None
        if not isinstance(data, dict):
            raise CongressSourceError("Respuesta inesperada del detalle de expediente.")
        return data

    def download_document(self, url: str, captcha_token: str = "") -> tuple[bytes, str]:
        """Descarga primero el archivo público oficial; el CAPTCHA queda solo como respaldo."""
        try:
            response = self._request(url)
        except CongressSourceError:
            if not captcha_token:
                raise
            response = self._request(url, headers={"X-Captcha-Token": captcha_token})
        if not isinstance(response, tuple):
            if captcha_token:
                response = self._request(url, headers={"X-Captcha-Token": captcha_token})
            if not isinstance(response, tuple):
                raise CongressSourceError("Se esperaba un PDF público, pero el servidor devolvió JSON.")
        body, headers = response
        return body, headers.get("Content-Disposition", "")
