"""Cliente HTTP unico: huella de navegador real, reintentos, rate limit, crudo a disco."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from curl_cffi import requests

DEFAULT_IMPERSONATE = "chrome131"


@dataclass
class RawResponse:
    url: str
    status: int
    body: bytes
    fetched_at: str


class HTTPStatusError(RuntimeError):
    """Respuesta HTTP no valida, conservando el cuerpo para diagnosticar bloqueos."""

    def __init__(self, url: str, status: int, body: bytes):
        super().__init__(f"HTTP {status} al pedir {url}")
        self.url = url
        self.status = status
        self.body = body


class Fetcher:
    """Un Fetcher por dominio: guarda su propio ritmo de peticiones."""

    def __init__(self, rate_per_sec: float = 2.0, impersonate: str = DEFAULT_IMPERSONATE,
                 headers: dict | None = None, timeout: int = 25,
                 cookies: dict | None = None):
        if rate_per_sec <= 0:
            raise ValueError("rate_per_sec debe ser mayor que cero")
        self.min_gap = 1.0 / rate_per_sec
        self.impersonate = impersonate
        self.timeout = timeout
        self.headers = headers or {}
        self._last = 0.0
        self.session = requests.Session(impersonate=impersonate)
        for nombre, valor in (cookies or {}).items():
            self.session.cookies.set(nombre, valor)

    def cambia_ritmo(self, rate_per_sec: float) -> None:
        """Baja (o sube) el ritmo **sin tirar la sesion**.

        Existe por lo que paso el 20 de septiembre de 2026. Ese dia Carrefour no
        dio ni un 403 en las 653 categorias; solo fallaron cuatro, tres con HTTP
        500 y una con 520. Entonces empezo el rescate, que hasta ahora creaba un
        `Fetcher` nuevo para ir mas despacio, y las cuatro dieron **403 a la
        primera**: "rescatadas 0 de 4".

        Un `Fetcher` nuevo es una `Session` nueva, y una `Session` nueva no lleva
        las cookies de Cloudflare (`__cf_bm` y compania) que el recorrido se
        habia ganado durante media hora de navegacion limpia. O sea que el
        rescate se presentaba como un desconocido justo despues de que nos
        acabaran de dar por buenos, y lo tomaban por lo que parecia.

        Ir mas despacio es una propiedad del ritmo, no de la identidad. Se
        cambia el ritmo y se conserva quien eres.
        """
        if rate_per_sec <= 0:
            raise ValueError("rate_per_sec debe ser mayor que cero")
        self.min_gap = 1.0 / rate_per_sec

    def _wait(self) -> None:
        gap = time.monotonic() - self._last
        sleep = self.min_gap - gap + random.uniform(0, self.min_gap * 0.4)
        if sleep > 0:
            time.sleep(sleep)
        self._last = time.monotonic()

    def request(self, method: str, url: str, *, retries: int = 3, **kw) -> RawResponse:
        """Peticion con ritmo, reintentos y rechazo explicito de estados HTTP malos."""
        if retries < 1:
            raise ValueError("retries debe ser al menos 1")
        last_exc = None
        last_status = None
        last_error_response = None
        extra_headers = kw.pop("headers", None) or {}
        headers = {**self.headers, **extra_headers}
        timeout = kw.pop("timeout", self.timeout)
        for attempt in range(retries):
            self._wait()
            try:
                r = self.session.request(method, url, timeout=timeout,
                                         headers=headers, **kw)
                # El 403 NO se reintenta aqui, y eso costo una medicion.
                #
                # Cloudflare y AWS WAF contestan 403 cuando te tienen fichado un
                # rato, asi que parecia obvio reintentar con espera: el 18 de
                # septiembre de 2026 Carrefour dio 403 en 373 de sus 653
                # categorias y el bloqueo se levanto solo a los veinte minutos.
                # Se puso una espera de 15 s y otra de 30 s por peticion.
                #
                # Medido contra un servidor de mentira que bloquea de verdad:
                # **45 segundos por categoria bloqueada**. Con las 373 de aquel
                # dia son cuatro horas y media durmiendo, en una tarea que
                # entera dura treinta y ocho minutos. El "arreglo" habria dejado
                # la ejecucion sin terminar nunca.
                #
                # El error de fondo era tener dos mecanismos esperando por lo
                # mismo. Quien espera es el colector, en `carrefour.recorre`:
                # apunta las categorias que fallan y vuelve a por ellas en
                # tandas, esperando **una vez para todo el grupo** en vez de una
                # vez por peticion. Aqui el 403 se levanta al momento y ya.
                if r.status_code in (429, 500, 502, 503, 504):
                    last_status = r.status_code
                    last_error_response = r
                    retry_after = r.headers.get("Retry-After", "")
                    try:
                        espera = max(0, min(float(retry_after), 120))
                    except ValueError:
                        espera = 2 ** attempt + random.random()
                    time.sleep(espera)
                    continue
                if r.status_code >= 400:
                    raise HTTPStatusError(str(r.url), r.status_code, r.content)
                return RawResponse(
                    url=str(r.url),
                    status=r.status_code,
                    body=r.content,
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                )
            except HTTPStatusError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                last_error_response = None
                if attempt + 1 < retries:
                    time.sleep(2 ** attempt + random.random())
        if last_error_response is not None:
            raise HTTPStatusError(
                str(last_error_response.url),
                last_error_response.status_code,
                last_error_response.content,
            )
        detalle = f" (ultimo HTTP {last_status})" if last_status else ""
        raise RuntimeError(
            f"fetch fallido tras {retries} intentos: {url}{detalle}"
        ) from last_exc

    def get(self, url: str, *, retries: int = 3, **kw) -> RawResponse:
        return self.request("GET", url, retries=retries, **kw)

    def put(self, url: str, *, retries: int = 3, **kw) -> RawResponse:
        return self.request("PUT", url, retries=retries, **kw)
