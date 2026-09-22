"""El cliente HTTP no puede convertir una pagina de error en datos crudos validos."""

from types import SimpleNamespace

import pytest

from core.fetch import Fetcher, HTTPStatusError


def respuesta(status: int, body: bytes = b"ok") -> SimpleNamespace:
    return SimpleNamespace(
        status_code=status,
        content=body,
        headers={},
        url="https://example.test/final",
    )


def test_rechaza_rate_limit_invalido():
    with pytest.raises(ValueError, match="mayor que cero"):
        Fetcher(rate_per_sec=0)


def test_un_404_es_error_y_no_se_parsea(monkeypatch):
    f = Fetcher(rate_per_sec=1000)
    llamadas = []
    monkeypatch.setattr(f.session, "request", lambda *a, **k: llamadas.append(a) or respuesta(404))

    with pytest.raises(RuntimeError, match="HTTP 404"):
        f.get("https://example.test/no-existe")
    assert len(llamadas) == 1


def test_reintenta_un_503_y_conserva_cabeceras(monkeypatch):
    f = Fetcher(rate_per_sec=1000, headers={"User-Agent": "navegador"})
    respuestas = iter([respuesta(503), respuesta(200, b"datos")])
    cabeceras = []

    def pedir(*args, **kwargs):
        cabeceras.append(kwargs["headers"])
        return next(respuestas)

    monkeypatch.setattr(f.session, "request", pedir)
    monkeypatch.setattr("core.fetch.time.sleep", lambda _: None)
    r = f.get("https://example.test/datos", headers={"Accept": "application/json"})

    assert r.body == b"datos"
    assert cabeceras == [
        {"User-Agent": "navegador", "Accept": "application/json"},
        {"User-Agent": "navegador", "Accept": "application/json"},
    ]


def test_conserva_el_cuerpo_del_ultimo_503(monkeypatch):
    f = Fetcher(rate_per_sec=1000)
    monkeypatch.setattr(
        f.session, "request", lambda *a, **k: respuesta(503, b"cloudflare challenge")
    )
    monkeypatch.setattr("core.fetch.time.sleep", lambda _: None)

    with pytest.raises(HTTPStatusError) as capturado:
        f.get("https://example.test/bloqueado")
    assert capturado.value.status == 503
    assert capturado.value.body == b"cloudflare challenge"


def test_permite_timeout_especifico_sin_duplicar_argumento(monkeypatch):
    f = Fetcher(rate_per_sec=1000, timeout=25)
    vistos = []

    def pedir(*args, **kwargs):
        vistos.append(kwargs["timeout"])
        return respuesta(200)

    monkeypatch.setattr(f.session, "request", pedir)
    f.put("https://example.test/config", timeout=5, json={"x": 1})
    assert vistos == [5]


def test_cambiar_el_ritmo_no_cambia_la_sesion():
    """Ir mas despacio no puede costar la identidad.

    El rescate de Carrefour baja el ritmo entre vuelta y vuelta. Si eso
    estrenara sesion, tiraria las cookies de Cloudflare que el recorrido se ha
    ganado -- que es exactamente lo que paso el 20 de septiembre de 2026.
    """
    f = Fetcher(rate_per_sec=2.0)
    sesion = f.session
    f.cambia_ritmo(0.5)
    assert f.session is sesion
    assert f.min_gap == 2.0


def test_un_ritmo_imposible_se_rechaza_tambien_al_cambiarlo():
    f = Fetcher(rate_per_sec=2.0)
    with pytest.raises(ValueError):
        f.cambia_ritmo(0)
